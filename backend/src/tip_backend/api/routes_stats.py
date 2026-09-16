from __future__ import annotations

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends

from .. import storage
from .deps import get_es

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
async def summary(es: AsyncElasticsearch = Depends(get_es)):
    return await storage.stats_summary(es)


@router.get("/by-region")
async def by_region(es: AsyncElasticsearch = Depends(get_es)):
    return await storage.stats_by_region(es)


@router.get("/top-sources")
async def top_sources(es: AsyncElasticsearch = Depends(get_es)):
    return await storage.top_sources(es)


@router.get("/top-malware-families")
async def top_malware_families(es: AsyncElasticsearch = Depends(get_es)):
    return await storage.top_malware_families(es)
