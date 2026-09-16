"""Environment-driven settings — every value has a sane default for
`docker compose up` with no .env file, so the stack runs out of the box."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIP_")

    elasticsearch_url: str = "http://elasticsearch:9200"
    indicators_index: str = "tip-indicators"

    collection_interval_minutes: int = 15
    ioc_retention_days: int = 30

    # ip-api.com's free tier: no key, but capped at 45 req/min and HTTP only
    # (not HTTPS) for non-commercial use — see geo.py for how the rate
    # limit is respected.
    geo_api_base_url: str = "http://ip-api.com/json"
    # Kept below the nominal 45/min — real 429s showed up even at 40/min in
    # practice (see geo.py's module docstring for why).
    geo_requests_per_minute: int = 30
    # Bounds a single collection run's worst-case time: any new (never
    # before seen) IPs beyond this count just wait for the next run rather
    # than making one run take hours against a 40/min rate limit.
    geo_max_new_lookups_per_run: int = 150

    cors_allow_origins: list[str] = ["*"]


settings = Settings()
