"""Deduplication and scoring — the same two stages from the CLI pipeline
prototype (github.com/NadiaLiaquat/threat-intel-pipeline), reimplemented
here against this platform's richer schema (multiple sources can now each
carry their own confidence and malware-family data).
"""
from __future__ import annotations

from .models import Indicator

_SEVERITY_BY_THREAT_TYPE = {
    "c2": 90.0,
    "botnet_cc": 90.0,
    "payload_delivery": 70.0,
    "malware_download": 70.0,
    "phishing": 55.0,
}
_DEFAULT_SEVERITY = 35.0


def dedupe(indicators: list[Indicator]) -> list[Indicator]:
    merged: dict[tuple[str, str], Indicator] = {}

    for ind in indicators:
        key = (ind.type, ind.indicator.strip().lower())
        existing = merged.get(key)

        if existing is None:
            merged[key] = ind
            continue

        existing.first_seen = min(existing.first_seen, ind.first_seen)
        existing.last_seen = max(existing.last_seen, ind.last_seen)
        for source in ind.sources:
            if source not in existing.sources:
                existing.sources.append(source)
        for tag in ind.tags:
            if tag not in existing.tags:
                existing.tags.append(tag)
        for note in ind.raw_context:
            if note and note not in existing.raw_context:
                existing.raw_context.append(note)
        existing.malware_family = existing.malware_family or ind.malware_family
        existing.threat_type = existing.threat_type or ind.threat_type
        existing.geo = existing.geo or ind.geo
        if ind.confidence is not None:
            existing.confidence = max(existing.confidence or 0, ind.confidence)

    return list(merged.values())


def score(indicators: list[Indicator]) -> list[Indicator]:
    for ind in indicators:
        corroboration = min(len(ind.sources), 3) / 3 * 100
        source_confidence = ind.confidence if ind.confidence is not None else 0.0
        family_bonus = 20.0 if ind.malware_family else 0.0

        ind.confidence = round(min(0.5 * source_confidence + 0.35 * corroboration + 0.15 * family_bonus / 20 * 100, 100), 1)
        ind.severity = _SEVERITY_BY_THREAT_TYPE.get(ind.threat_type or "", _DEFAULT_SEVERITY)

    return indicators
