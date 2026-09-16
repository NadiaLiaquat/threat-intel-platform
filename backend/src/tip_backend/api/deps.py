"""Shared FastAPI dependencies — one Elasticsearch client for the app's
lifetime, injected into routes rather than constructed per-request."""
from __future__ import annotations

from typing import AsyncIterator

from elasticsearch import AsyncElasticsearch
from fastapi import Request


async def get_es(request: Request) -> AsyncIterator[AsyncElasticsearch]:
    yield request.app.state.es
