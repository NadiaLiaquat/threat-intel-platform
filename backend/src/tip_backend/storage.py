"""Repository layer — the only module that speaks Elasticsearch query DSL.
Everything else (API routes, the pipeline) works with plain Indicator
objects and plain dicts.
"""
from __future__ import annotations

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from .config import settings
from .models import Indicator


def _to_doc(ind: Indicator) -> dict:
    doc = ind.model_dump()
    geo = doc.get("geo")
    if geo and geo.get("lat") is not None and geo.get("lon") is not None:
        geo["location"] = {"lat": geo["lat"], "lon": geo["lon"]}
    return doc


async def upsert_many(es: AsyncElasticsearch, indicators: list[Indicator]) -> int:
    if not indicators:
        return 0
    actions = (
        {"_op_type": "index", "_index": settings.indicators_index, "_id": ind.doc_id(), "_source": _to_doc(ind)}
        for ind in indicators
    )
    success_count, _errors = await async_bulk(es, actions)
    return success_count


async def search(
    es: AsyncElasticsearch,
    *,
    ioc_type: str | None = None,
    query: str | None = None,
    min_confidence: float | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[dict], int]:
    must: list[dict] = []
    if ioc_type:
        must.append({"term": {"type": ioc_type}})
    if min_confidence is not None:
        must.append({"range": {"confidence": {"gte": min_confidence}}})
    if query:
        must.append({"wildcard": {"indicator": {"value": f"*{query}*", "case_insensitive": True}}})

    body = {"query": {"bool": {"must": must}} if must else {"match_all": {}}}

    resp = await es.search(
        index=settings.indicators_index,
        query=body["query"],
        sort=[{"severity": "desc"}, {"confidence": "desc"}],
        from_=(page - 1) * page_size,
        size=page_size,
    )
    hits = resp["hits"]
    total = hits["total"]["value"]
    docs = [{"id": h["_id"], **h["_source"]} for h in hits["hits"]]
    return docs, total


async def stats_summary(es: AsyncElasticsearch) -> dict:
    resp = await es.search(
        index=settings.indicators_index,
        size=0,
        aggs={
            "by_type": {"terms": {"field": "type", "size": 10}},
            "avg_confidence": {"avg": {"field": "confidence"}},
            "avg_severity": {"avg": {"field": "severity"}},
        },
    )
    total = resp["hits"]["total"]["value"]
    by_type = {b["key"]: b["doc_count"] for b in resp["aggregations"]["by_type"]["buckets"]}
    return {
        "total_indicators": total,
        "by_type": by_type,
        "avg_confidence": round(resp["aggregations"]["avg_confidence"]["value"] or 0, 1),
        "avg_severity": round(resp["aggregations"]["avg_severity"]["value"] or 0, 1),
    }


async def stats_by_region(es: AsyncElasticsearch, size: int = 50) -> list[dict]:
    resp = await es.search(
        index=settings.indicators_index,
        size=0,
        query={"exists": {"field": "geo.country_code"}},
        aggs={"by_country": {"terms": {"field": "geo.country_code", "size": size}}},
    )
    return [
        {"country_code": b["key"], "count": b["doc_count"]}
        for b in resp["aggregations"]["by_country"]["buckets"]
    ]


async def top_sources(es: AsyncElasticsearch, size: int = 10) -> list[dict]:
    resp = await es.search(
        index=settings.indicators_index,
        size=0,
        aggs={"by_source": {"terms": {"field": "sources", "size": size}}},
    )
    return [{"source": b["key"], "count": b["doc_count"]} for b in resp["aggregations"]["by_source"]["buckets"]]


async def top_malware_families(es: AsyncElasticsearch, size: int = 10) -> list[dict]:
    resp = await es.search(
        index=settings.indicators_index,
        size=0,
        query={"exists": {"field": "malware_family"}},
        aggs={"by_family": {"terms": {"field": "malware_family", "size": size}}},
    )
    return [
        {"family": b["key"], "count": b["doc_count"]}
        for b in resp["aggregations"]["by_family"]["buckets"]
    ]
