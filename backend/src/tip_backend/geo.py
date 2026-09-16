"""IP geolocation via ip-api.com's free tier — no API key, nominally capped
at 45 requests/minute for non-commercial use. GeoLocator self-throttles to
a configurable, more conservative rate (settings.geo_requests_per_minute,
default 30/min) — running this against live traffic surfaced real 429
responses even at 40/min, meaning the effective limit in practice (likely
enforced per source IP, which may be shared/NAT'd) is tighter than the
nominal figure. A single 429 gets one retry, backing off by the
`Retry-After` header if the response includes one, else a fixed 5s;
anything beyond that is treated as "no geo data available this run", not
an error — the caller's per-run cap (see pipeline_run.py) means it'll
simply be tried again on a later run rather than blocking this one.

Domains and URLs are geolocated by best-effort DNS resolution to an IP
first (see resolve_host_ip) — this can fail (rotating IPs, no DNS, etc.)
and callers should treat a None result as "no geo data available", not
an error. Note: as of this build, only IP-type indicators are actually
routed through geo enrichment (see pipeline_run.py's _enrich_geo) —
resolve_host_ip is kept here as a correct, tested, standalone utility for
anyone wiring domain/URL geolocation back in deliberately.
"""
from __future__ import annotations

import asyncio
import socket
import time
from urllib.parse import urlparse

import httpx

from .config import settings
from .models import GeoInfo

_DEFAULT_RETRY_AFTER_SECONDS = 5.0


class GeoLocator:
    def __init__(self, requests_per_minute: int | None = None, base_url: str | None = None):
        rpm = requests_per_minute or settings.geo_requests_per_minute
        self._min_interval = 60.0 / rpm
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

    async def _request_once(self, ip: str, client: httpx.AsyncClient) -> httpx.Response | None:
        await self._throttle()
        try:
            return await client.get(
                f"{self._base_url}/{ip}",
                params={"fields": "status,country,countryCode,city,lat,lon,isp,as"},
            )
        except httpx.HTTPError:
            return None

    async def lookup(self, ip: str, client: httpx.AsyncClient | None = None) -> GeoInfo | None:
        owns_client = client is None
        client = client or httpx.AsyncClient(timeout=5.0)
        try:
            resp = await self._request_once(ip, client)

            if resp is not None and resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", _DEFAULT_RETRY_AFTER_SECONDS))
                await asyncio.sleep(retry_after)
                resp = await self._request_once(ip, client)

            if resp is None or resp.status_code != 200:
                return None

            try:
                data = resp.json()
            except ValueError:
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
