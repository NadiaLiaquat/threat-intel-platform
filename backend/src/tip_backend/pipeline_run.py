"""Orchestrates one full collection run: gather from every source
concurrently, dedupe, geolocate IP-type indicators (reusing already-known
geo data from Elasticsearch so the rate-limited free geo API is only ever
called for genuinely new IPs), score, and persist.
"""
from __future__ import annotations

import asyncio
import logging

import httpx
from elasticsearch import AsyncElasticsearch

from .collectors import ALL_COLLECTORS
from .collectors.base import Collector
from .config import settings
from .geo import GeoLocator
from .models import GeoInfo, Indicator
from .processing import dedupe, score
from .storage import upsert_many

logger = logging.getLogger(__name__)

_geo_locator = GeoLocator()


async def _collect_all(collectors: list[Collector]) -> list[Indicator]:
    async with httpx.AsyncClient(headers={"User-Agent": "threat-intel-platform/0.1"}) as client:

        async def _safe_collect(c: Collector) -> list[Indicator]:
            try:
                results = await c.collect(client)
                logger.info("collected %d indicators from %s", len(results), c.name)
                return results
            except Exception:  # noqa: BLE001 - one source failing must not sink the run
                logger.exception("collector %s failed; continuing without it", c.name)
                return []

        results = await asyncio.gather(*(_safe_collect(c) for c in collectors))
    return [ind for batch in results for ind in batch]


async def _existing_geo(es: AsyncElasticsearch, ip_indicators: list[Indicator]) -> dict[str, GeoInfo]:
    """Pre-load geo data Elasticsearch already has, keyed by the IP value
    itself (not the indicator's doc_id) — so it's shared across every
    indicator that happens to be that same IP, not just re-fetched of the
    exact same document."""
    doc_ids = list({ind.doc_id() for ind in ip_indicators})
    if not doc_ids:
        return {}
    resp = await es.mget(index="tip-indicators", ids=doc_ids)
    known: dict[str, GeoInfo] = {}
    for doc in resp["docs"]:
        if doc.get("found") and doc["_source"].get("geo"):
            known[doc["_source"]["indicator"]] = GeoInfo(**doc["_source"]["geo"])
    return known


async def _enrich_geo(es: AsyncElasticsearch, indicators: list[Indicator]) -> None:
    """Geolocates IP-type indicators only. Domains/URLs are deliberately
    not DNS-resolved for geo purposes — see the README: it's an unreliable
    signal (shared hosting/CDNs) and was, in practice, the single biggest
    performance cost of a collection run before this was scoped down."""
    ip_indicators = [i for i in indicators if i.type == "ip" and i.geo is None]
    known = await _existing_geo(es, ip_indicators)
    new_lookups = 0

    async with httpx.AsyncClient(timeout=5.0) as client:
        for ind in ip_indicators:
            cached = known.get(ind.indicator)
            if cached is not None:
                ind.geo = cached
                continue

            if new_lookups >= settings.geo_max_new_lookups_per_run:
                continue  # picked up on a future run instead

            geo = await _geo_locator.lookup(ind.indicator, client=client)
            new_lookups += 1
            if geo is not None:
                ind.geo = geo
                known[ind.indicator] = geo  # reuse within this same run too


async def run_once(es: AsyncElasticsearch) -> dict:
    raw = await _collect_all(ALL_COLLECTORS)
    deduped = dedupe(raw)
    await _enrich_geo(es, deduped)
    scored = score(deduped)
    indexed = await upsert_many(es, scored)

    summary = {"collected": len(raw), "deduped": len(deduped), "indexed": indexed}
    logger.info("pipeline run complete: %s", summary)
    return summary
