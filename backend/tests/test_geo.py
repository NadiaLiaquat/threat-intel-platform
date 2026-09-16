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


@pytest.mark.asyncio
@respx.mock
async def test_geo_locator_retries_once_after_429_then_succeeds():
    route = respx.get("http://ip-api.com/json/8.8.8.8").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"status": "success", "countryCode": "US"}),
        ]
    )
    locator = GeoLocator(requests_per_minute=6000)  # throttle interval irrelevant here
    geo = await locator.lookup("8.8.8.8")
    assert route.call_count == 2
    assert geo is not None
    assert geo.country_code == "US"


@pytest.mark.asyncio
@respx.mock
async def test_geo_locator_gives_up_after_second_429():
    route = respx.get("http://ip-api.com/json/8.8.4.4").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"})
    )
    locator = GeoLocator(requests_per_minute=6000)
    geo = await locator.lookup("8.8.4.4")
    assert route.call_count == 2  # one retry, then gives up — no infinite loop
    assert geo is None
