"""These hit the real, live abuse.ch feeds — no mocking, no API keys.
Marked `live` so a fully offline test run can skip them
(`pytest -m "not live"`), but they're what actually proves the parsing
logic works against real-world data, not a fixture I made up.
"""
import httpx
import pytest

from tip_backend.collectors import (
    FeodoTrackerCollector,
    MalwareBazaarCollector,
    ThreatFoxCollector,
    UrlhausCollector,
)

pytestmark = pytest.mark.live


@pytest.fixture
async def client():
    async with httpx.AsyncClient(headers={"User-Agent": "threat-intel-platform-tests/0.1"}) as c:
        yield c


@pytest.mark.asyncio
async def test_urlhaus_returns_url_indicators(client):
    results = await UrlhausCollector().collect(client)
    assert len(results) > 0
    assert all(r.type == "url" for r in results)
    assert all(r.indicator.startswith(("http://", "https://")) for r in results)


@pytest.mark.asyncio
async def test_threatfox_returns_multiple_ioc_types(client):
    results = await ThreatFoxCollector().collect(client)
    assert len(results) > 0
    types_seen = {r.type for r in results}
    # A live feed will vary run to run, but across a day's worth of IOCs
    # it should span at least a couple of the platform's IOC types.
    assert len(types_seen) >= 2
    assert types_seen <= {"ip", "domain", "url", "hash_md5", "hash_sha1", "hash_sha256"}


@pytest.mark.asyncio
async def test_malwarebazaar_returns_all_three_hash_types(client):
    results = await MalwareBazaarCollector().collect(client)
    assert len(results) > 0
    types_seen = {r.type for r in results}
    assert types_seen == {"hash_md5", "hash_sha1", "hash_sha256"}
    sha256 = next(r for r in results if r.type == "hash_sha256")
    assert len(sha256.indicator) == 64


@pytest.mark.asyncio
async def test_feodotracker_returns_ip_indicators_with_geo(client):
    results = await FeodoTrackerCollector().collect(client)
    assert len(results) > 0
    assert all(r.type == "ip" for r in results)
    assert any(r.geo is not None for r in results)  # this feed bundles country data
