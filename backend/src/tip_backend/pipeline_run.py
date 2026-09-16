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
from .geo import GeoLocator, resolve_host_ip
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


async def _existing_geo(es: AsyncElasticsearch, indicators: list[Indicator]) -> dict[str, GeoInfo]:
    doc_ids = list({ind.doc_id() for ind in indicators if ind.type == "ip"})
    if not doc_ids:
        return {}
    resp = await es.mget(index="tip-indicators", ids=doc_ids)
    known: dict[str, GeoInfo] = {}
    for doc in resp["docs"]:
        if doc.get("found") and doc["_source"].get("geo"):
            known[doc["_id"]] = GeoInfo(**doc["_source"]["geo"])
    return known


async def _enrich_geo(es: AsyncElasticsearch, indicators: list[Indicator]) -> None:
    known = await _existing_geo(es, indicators)

    async with httpx.AsyncClient(timeout=5.0) as client:
        for ind in indicators:
            if ind.geo is not None:
                continue  # already has geo (e.g. Feodo Tracker's bundled country)

            cached = known.get(ind.doc_id())
            if cached is not None:
                ind.geo = cached
                continue

            ip = ind.indicator if ind.type == "ip" else resolve_host_ip(ind.indicator)
            if ip is None:
                continue

            geo = await _geo_locator.lookup(ip, client=client)
            if geo is not None:
                ind.geo = geo
                known[ind.doc_id()] = geo  # reuse within this same run too


async def run_once(es: AsyncElasticsearch) -> dict:
    raw = await _collect_all(ALL_COLLECTORS)
    deduped = dedupe(raw)
    await _enrich_geo(es, deduped)
    scored = score(deduped)
    indexed = await upsert_many(es, scored)

    summary = {"collected": len(raw), "deduped": len(deduped), "indexed": indexed}
    logger.info("pipeline run complete: %s", summary)
    return summary
