"""The IOC schema every stage after collection agrees on, and the single
place indicator "type" is defined for the whole platform: IP, URL, domain,
and all three common hash types."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

IocType = Literal["ip", "url", "domain", "hash_md5", "hash_sha1", "hash_sha256"]


class GeoInfo(BaseModel):
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    isp: Optional[str] = None
    as_name: Optional[str] = None


class Indicator(BaseModel):
    indicator: str
    type: IocType
    first_seen: str  # ISO-8601 UTC
    last_seen: str  # ISO-8601 UTC
    sources: list[str] = Field(default_factory=list)
    malware_family: Optional[str] = None
    threat_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    severity: Optional[float] = None
    geo: Optional[GeoInfo] = None
    raw_context: list[str] = Field(default_factory=list)

    def doc_id(self) -> str:
        return f"{self.type}:{self.indicator}"
