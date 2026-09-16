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
    geo_requests_per_minute: int = 40

    cors_allow_origins: list[str] = ["*"]


settings = Settings()
