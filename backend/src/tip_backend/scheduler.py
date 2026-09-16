"""Standalone collector process — runs the pipeline immediately on start,
then on a fixed interval, forever. This is deliberately a separate
container/process from the API (see docker-compose.yml) so collection
keeps running on schedule independent of API traffic.
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from .es_client import ensure_index, get_client
from .pipeline_run import run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def _job() -> None:
    es = get_client()
    try:
        await ensure_index(es)
        await run_once(es)
    finally:
        await es.close()


async def main() -> None:
    logger.info(
        "starting collector: interval=%dmin, elasticsearch=%s",
        settings.collection_interval_minutes,
        settings.elasticsearch_url,
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(_job, "interval", minutes=settings.collection_interval_minutes, next_run_time=None)
    scheduler.start()

    await _job()  # run immediately on startup, don't wait for the first interval

    try:
        await asyncio.Event().wait()  # keep the process alive
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
