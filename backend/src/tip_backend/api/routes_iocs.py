from __future__ import annotations

from typing import Optional

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, Query

from .. import storage
from .deps import get_es

router = APIRouter(prefix="/api/iocs", tags=["iocs"])


@router.get("")
async def list_iocs(
    type: Optional[str] = Query(None, description="ip | url | domain | hash_md5 | hash_sha1 | hash_sha256"),
    q: Optional[str] = Query(None, description="substring search on the indicator value"),
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    es: AsyncElasticsearch = Depends(get_es),
):
    docs, total = await storage.search(
        es, ioc_type=type, query=q, min_confidence=min_confidence, page=page, page_size=page_size
    )
    return {"results": docs, "total": total, "page": page, "page_size": page_size}
