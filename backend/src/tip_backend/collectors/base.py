"""Shared collector interface. Every collector fetches its source's real,
live, public, no-API-key feed and returns normalized Indicator objects —
no mock data anywhere in this module or its subclasses."""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ..models import Indicator


class Collector(ABC):
    name: str

    @abstractmethod
    async def collect(self, client: httpx.AsyncClient) -> list[Indicator]:
        """Fetch and normalize this source's current feed."""
        raise NotImplementedError
