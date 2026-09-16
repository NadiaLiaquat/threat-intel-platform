"""Regression test for a real bug caught while running this against live
data: geo lookups were cached by the indicator's own doc_id, so many
different indicators resolving to (or literally being) the same IP each
triggered their own call to the rate-limited free geo API instead of
sharing one cached result. Fixed by keying the cache on the IP value
itself. See pipeline_run.py's _enrich_geo/_existing_geo docstrings.
"""
import httpx
import pytest
import respx

from tip_backend.models import Indicator
from tip_backend.pipeline_run import _enrich_geo


class _FakeAsyncElasticsearch:
    """Just enough of the client's interface for _existing_geo's mget call —
    reports nothing pre-cached, forcing every lookup through the geo API."""

    async def mget(self, index, ids):
        return {"docs": [{"_id": i, "found": False} for i in ids]}


@pytest.mark.asyncio
@respx.mock
async def test_enrich_geo_calls_the_api_once_per_unique_ip():
    call_count = {"n": 0}

    def _responder(request):
        call_count["n"] += 1
        return httpx.Response(
            200,
            json={
                "status": "success",
                "country": "United States",
                "countryCode": "US",
                "city": "Ashburn",
                "lat": 39.0,
                "lon": -77.5,
                "isp": "Example",
                "as": "AS0 Example",
            },
        )

    respx.get(url__regex=r"http://ip-api\.com/json/.*").mock(side_effect=_responder)

    # Five distinct indicators, but only two unique IPs between them.
    indicators = [
        Indicator(indicator="1.2.3.4", type="ip", first_seen="t", last_seen="t"),
        Indicator(indicator="1.2.3.4", type="ip", first_seen="t", last_seen="t"),
        Indicator(indicator="1.2.3.4", type="ip", first_seen="t", last_seen="t"),
        Indicator(indicator="5.6.7.8", type="ip", first_seen="t", last_seen="t"),
        Indicator(indicator="5.6.7.8", type="ip", first_seen="t", last_seen="t"),
    ]

    await _enrich_geo(_FakeAsyncElasticsearch(), indicators)

    assert call_count["n"] == 2  # not 5
    assert all(ind.geo is not None and ind.geo.country_code == "US" for ind in indicators)


@pytest.mark.asyncio
async def test_enrich_geo_skips_non_ip_types_entirely():
    """Domains/URLs are not geolocated — see the module docstring for why."""
    indicators = [
        Indicator(indicator="evil.example.com", type="domain", first_seen="t", last_seen="t"),
        Indicator(indicator="http://evil.example.com/x", type="url", first_seen="t", last_seen="t"),
    ]
    await _enrich_geo(_FakeAsyncElasticsearch(), indicators)
    assert all(ind.geo is None for ind in indicators)
