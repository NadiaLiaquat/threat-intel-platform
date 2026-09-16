"""ThreatFox (abuse.ch) — mixed-type IOCs (IP, domain, URL, hashes) tied
to malware families, with a confidence figure the source itself assigns.
Uses the public bulk export (no Auth-Key needed), not the POST API, which
abuse.ch now gates behind free registration at auth.abuse.ch.
https://threatfox.abuse.ch/export/
"""
from __future__ import annotations

import httpx

from ..dateutils import parse_dt, now_iso
from ..models import Indicator, IocType
from .base import Collector

FEED_URL = "https://threatfox.abuse.ch/export/json/recent/"

_TYPE_MAP: dict[str, IocType] = {
    "domain": "domain",
    "url": "url",
    "md5_hash": "hash_md5",
    "sha1_hash": "hash_sha1",
    "sha256_hash": "hash_sha256",
    # "ip:port" is handled separately below — it needs splitting, not a
    # direct lookup.
}


class ThreatFoxCollector(Collector):
    name = "threatfox"

    async def collect(self, client: httpx.AsyncClient) -> list[Indicator]:
        resp = await client.get(FEED_URL, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()

        indicators: list[Indicator] = []
        for entries in data.values():
            for entry in entries:
                indicator = self._to_indicator(entry)
                if indicator is not None:
                    indicators.append(indicator)
        return indicators

    def _to_indicator(self, entry: dict) -> Indicator | None:
        raw_type = entry.get("ioc_type")
        value = entry.get("ioc_value", "")

        if raw_type == "ip:port":
            ioc_type: IocType = "ip"
            value = value.split(":", 1)[0]
        else:
            ioc_type = _TYPE_MAP.get(raw_type)  # type: ignore[assignment]
            if ioc_type is None:
                return None  # e.g. "email", "cve" — outside this platform's four IOC types

        first_seen = parse_dt(entry.get("first_seen_utc")) or now_iso()
        last_seen = parse_dt(entry.get("last_seen_utc")) or first_seen
        tags = [t.strip() for t in (entry.get("tags") or "").split(",") if t.strip()]
        confidence = entry.get("confidence_level")

        return Indicator(
            indicator=value,
            type=ioc_type,
            first_seen=first_seen,
            last_seen=last_seen,
            sources=[self.name],
            malware_family=entry.get("malware_printable"),
            threat_type=entry.get("threat_type"),
            tags=tags,
            confidence=float(confidence) if confidence is not None else None,
        )
