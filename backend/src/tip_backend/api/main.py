from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..es_client import ensure_index, get_client
from ..pipeline_run import run_once
from . import routes_iocs, routes_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.es = get_client()
    await ensure_index(app.state.es)
    yield
    await app.state.es.close()


app = FastAPI(title="Threat Intelligence Platform API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_iocs.router)
app.include_router(routes_stats.router)

misc = APIRouter()


@misc.get("/api/health")
async def health():
    return {"status": "ok"}


@misc.post("/api/collect/run")
async def trigger_collection():
    """Run the collection pipeline immediately, on demand — used by the
    dashboard's manual refresh, and handy for local testing without
    waiting for the scheduled interval."""
    summary = await run_once(app.state.es)
    return {"status": "completed", **summary}


app.include_router(misc)
