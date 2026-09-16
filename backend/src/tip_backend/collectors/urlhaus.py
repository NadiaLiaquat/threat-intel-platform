"""URLhaus (abuse.ch) — recently reported malicious URLs. Free, public,
no API key. https://urlhaus.abuse.ch/api/
"""
from __future__ import annotations

import httpx

from ..dateutils import parse_dt, now_iso
from ..models import Indicator
from .base import Collector

FEED_URL = "https://urlhaus.abuse.ch/downloads/json_recent/"


class UrlhausCollector(Collector):
    name = "urlhaus"

    async def collect(self, client: httpx.AsyncClient) -> list[Indicator]:
        resp = await client.get(FEED_URL, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()

        indicators: list[Indicator] = []
        for entries in data.values():
            for entry in entries:
                first_seen = parse_dt(entry.get("dateadded")) or now_iso()
                last_seen = parse_dt(entry.get("last_online")) or first_seen
                indicators.append(
                    Indicator(
                        indicator=entry["url"],
                        type="url",
                        first_seen=first_seen,
                        last_seen=last_seen,
                        sources=[self.name],
                        threat_type=entry.get("threat"),
                        tags=list(entry.get("tags") or []),
                        raw_context=[f"status={entry.get('url_status')}", entry.get("urlhaus_link", "")],
                    )
                )
        return indicators
