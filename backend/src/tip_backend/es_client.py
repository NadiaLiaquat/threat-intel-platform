"""Elasticsearch connection and index bootstrapping."""
from __future__ import annotations

from elasticsearch import AsyncElasticsearch

from .config import settings

INDEX_MAPPING = {
    "properties": {
        "indicator": {"type": "keyword"},
        "type": {"type": "keyword"},
        "first_seen": {"type": "date"},
        "last_seen": {"type": "date"},
        "sources": {"type": "keyword"},
        "malware_family": {"type": "keyword"},
        "threat_type": {"type": "keyword"},
        "tags": {"type": "keyword"},
        "confidence": {"type": "float"},
        "severity": {"type": "float"},
        "raw_context": {"type": "text"},
        "geo": {
            "properties": {
                "country": {"type": "keyword"},
                "country_code": {"type": "keyword"},
                "city": {"type": "keyword"},
                "location": {"type": "geo_point"},
                "isp": {"type": "keyword"},
                "as_name": {"type": "keyword"},
            }
        },
    }
}


def get_client() -> AsyncElasticsearch:
    return AsyncElasticsearch(settings.elasticsearch_url)


async def ensure_index(es: AsyncElasticsearch) -> None:
    exists = await es.indices.exists(index=settings.indicators_index)
    if not exists:
        await es.indices.create(index=settings.indicators_index, mappings=INDEX_MAPPING)
