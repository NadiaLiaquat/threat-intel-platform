"""Feodo Tracker (abuse.ch) — known botnet C2 IPs (Emotet, QakBot, etc).
Free, public, no API key. Bonus: this feed already includes a country
code per IP, so these indicators get real region data without needing a
separate geolocation lookup. https://feodotracker.abuse.ch/
"""
from __future__ import annotations

import httpx

from ..dateutils import parse_dt, now_iso
from ..models import GeoInfo, Indicator
from .base import Collector

FEED_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"


class FeodoTrackerCollector(Collector):
    name = "feodotracker"

    async def collect(self, client: httpx.AsyncClient) -> list[Indicator]:
        resp = await client.get(FEED_URL, timeout=30.0)
        resp.raise_for_status()
        entries = resp.json()

        indicators: list[Indicator] = []
        for entry in entries:
            first_seen = parse_dt(entry.get("first_seen")) or now_iso()
            last_seen = parse_dt(entry.get("last_online")) or first_seen
            country_code = entry.get("country")

            indicators.append(
                Indicator(
                    indicator=entry["ip_address"],
                    type="ip",
                    first_seen=first_seen,
                    last_seen=last_seen,
                    sources=[self.name],
                    malware_family=entry.get("malware"),
                    threat_type="c2",
                    raw_context=[f"port={entry.get('port')}", f"status={entry.get('status')}"],
                    geo=GeoInfo(country_code=country_code) if country_code else None,
                )
            )
        return indicators
