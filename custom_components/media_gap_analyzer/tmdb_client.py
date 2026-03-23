"""TMDb API client for Suivi Médiathèque."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import TMDB_BASE_URL

_LOGGER = logging.getLogger(__name__)

# Rate-limit: max 40 req / 10 s  ->  ~0.25 s between calls is safe
_REQUEST_DELAY = 0.28


class TMDbClient:
    """Async client for The Movie Database API v3."""

    def __init__(self, hass: HomeAssistant, api_key: str, language: str = "fr") -> None:
        self._hass = hass
        self._api_key = api_key
        self._language = language
        self._session = async_get_clientsession(hass)
        self._cache: dict[str, Any] = {}
        self._last_request: float = 0

    async def _throttle(self) -> None:
        now = asyncio.get_event_loop().time()
        diff = now - self._last_request
        if diff < _REQUEST_DELAY:
            await asyncio.sleep(_REQUEST_DELAY - diff)
        self._last_request = asyncio.get_event_loop().time()

    async def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        cache_key = f"{path}|{params}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        await self._throttle()
        url = f"{TMDB_BASE_URL}{path}"
        base_params = {"api_key": self._api_key, "language": self._language}
        if params:
            base_params.update(params)

        try:
            async with self._session.get(url, params=base_params, timeout=15) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    _LOGGER.warning("TMDb rate limit hit, waiting %s s", retry_after)
                    await asyncio.sleep(retry_after)
                    return await self._get(path, params)
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json()
                self._cache[cache_key] = data
                return data
        except Exception as exc:
            _LOGGER.error("TMDb API error for %s: %s", path, exc)
            raise

    # -- public helpers --------------------------------------------------------

    async def validate_api_key(self) -> bool:
        try:
            data = await self._get("/configuration")
            return "images" in data
        except Exception:
            return False

    async def search_movie(self, name: str, year: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"query": name}
        if year:
            params["year"] = year
        data = await self._get("/search/movie", params)
        return data.get("results", [])

    async def get_movie(self, movie_id: int) -> dict[str, Any]:
        return await self._get(f"/movie/{movie_id}")

    async def get_collection(self, collection_id: int) -> dict[str, Any]:
        return await self._get(f"/collection/{collection_id}")

    async def search_tv(self, name: str, year: int | None = None) -> list[dict]:
        params: dict[str, Any] = {"query": name}
        if year:
            params["first_air_date_year"] = year
        data = await self._get("/search/tv", params)
        return data.get("results", [])

    async def get_tv(self, tv_id: int) -> dict[str, Any]:
        return await self._get(f"/tv/{tv_id}")

    async def get_tv_season(self, tv_id: int, season_number: int) -> dict[str, Any]:
        return await self._get(f"/tv/{tv_id}/season/{season_number}")

    def clear_cache(self) -> None:
        self._cache.clear()
