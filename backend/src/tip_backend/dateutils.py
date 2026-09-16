"""Every collector's source feed uses a slightly different timestamp
format; this is the one place that gets normalized to UTC ISO-8601 so
nothing downstream has to special-case it per source."""
from __future__ import annotations

from datetime import datetime, timezone

_FORMATS = (
    "%Y-%m-%d %H:%M:%S UTC",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


def parse_dt(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    for fmt in _FORMATS:
        try:
            dt = datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
