"""IP geolocation via ip-api.com's free tier — no API key, but capped at
45 requests/minute for non-commercial use. GeoLocator enforces a
configurable, slightly conservative rate limit itself (default 40/min)
so the platform never gets throttled or blocked outright.

Domains and URLs are geolocated by best-effort DNS resolution to an IP
first (see resolve_host_ip) — this can fail (rotating IPs, no DNS, etc.)
and callers should treat a None result as "no geo data available", not
an error.
"""
from __future__ import annotations

import asyncio
import socket
import time
from urllib.parse import urlparse

import httpx

from .config import settings
from .models import GeoInfo


class GeoLocator:
    def __init__(self, requests_per_minute: int = 40, base_url: str | None = None):
        self._min_interval = 60.0 / requests_per_minute
        self._base_url = base_url or settings.geo_api_base_url
        self._last_request_at = 0.0
        self._lock = asyncio.Lock()

    async def _throttle(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request_at
            wait = self._min_interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    async def lookup(self, ip: str, client: httpx.AsyncClient | None = None) -> GeoInfo | None:
        await self._throttle()
        owns_client = client is None
        client = client or httpx.AsyncClient(timeout=5.0)
        try:
            resp = await client.get(
                f"{self._base_url}/{ip}",
                params={"fields": "status,country,countryCode,city,lat,lon,isp,as"},
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return None
        finally:
            if owns_client:
                await client.aclose()

        if data.get("status") != "success":
            return None

        return GeoInfo(
            country=data.get("country"),
            country_code=data.get("countryCode"),
            city=data.get("city"),
            lat=data.get("lat"),
            lon=data.get("lon"),
            isp=data.get("isp"),
            as_name=data.get("as"),
        )


def resolve_host_ip(hostname_or_url: str) -> str | None:
    """Best-effort DNS resolution for a domain or URL's host, so
    non-IP indicators can still get a geo lookup. Returns None on any
    resolution failure rather than raising — DNS is unreliable by
    nature for indicators pulled from threat feeds."""
    host = hostname_or_url
    if "://" in host:
        host = urlparse(host).hostname or ""
    if not host:
        return None
    try:
        return socket.gethostbyname(host)
    except (socket.gaierror, UnicodeError):
        return None
