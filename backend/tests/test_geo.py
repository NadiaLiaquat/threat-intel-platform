import httpx
import pytest
import respx

from tip_backend.geo import GeoLocator, resolve_host_ip


def test_resolve_host_ip_handles_unresolvable_gracefully():
    assert resolve_host_ip("this-domain-should-never-resolve.invalid") is None


def test_resolve_host_ip_extracts_host_from_url():
    # example.com is a real, stable, reserved-for-documentation domain
    # (RFC 2606) that always resolves — safe to depend on in tests.
    assert resolve_host_ip("http://example.com/path") is not None


@pytest.mark.asyncio
@respx.mock
async def test_geo_locator_parses_successful_response():
    respx.get("http://ip-api.com/json/1.2.3.4").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "country": "United States",
                "countryCode": "US",
                "city": "Ashburn",
                "lat": 39.03,
                "lon": -77.5,
                "isp": "Amazon",
                "as": "AS14618 Amazon",
            },
        )
    )
    locator = GeoLocator(requests_per_minute=1000)
    geo = await locator.lookup("1.2.3.4")
    assert geo is not None
    assert geo.country_code == "US"
    assert geo.lat == 39.03


@pytest.mark.asyncio
@respx.mock
async def test_geo_locator_returns_none_on_failed_status():
    respx.get("http://ip-api.com/json/10.0.0.1").mock(
        return_value=httpx.Response(200, json={"status": "fail", "message": "private range"})
    )
    locator = GeoLocator(requests_per_minute=1000)
    assert await locator.lookup("10.0.0.1") is None
