"""DataUpdateCoordinator for Suivi Médiathèque."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .analyzer import AnalysisResult, MediaAnalyzer
from .const import (
    CONF_ANIME_PATHS,
    CONF_LANGUAGE,
    CONF_MOVIES_PATHS,
    CONF_NAS_PASSWORD,
    CONF_NAS_SERVER,
    CONF_NAS_USERNAME,
    CONF_SCAN_INTERVAL,
    CONF_SERIES_PATHS,
    CONF_TMDB_API_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .scanner import scan_movies, scan_series
from .tmdb_client import TMDbClient

_LOGGER = logging.getLogger(__name__)


class MediaGapCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates periodic media-library scans."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        interval_hours = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=interval_hours),
        )

    def _get_option(self, key: str, default: str = "") -> str:
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _async_update_data(self) -> dict[str, Any]:
        api_key = self.entry.data.get(CONF_TMDB_API_KEY, "")
        language = self.entry.data.get(CONF_LANGUAGE, "fr")

        client = TMDbClient(self.hass, api_key, language)

        movies_paths = self._get_option(CONF_MOVIES_PATHS)
        series_paths = self._get_option(CONF_SERIES_PATHS)
        anime_paths = self._get_option(CONF_ANIME_PATHS)

        # Build NAS config (None if no server configured)
        nas_server = self._get_option(CONF_NAS_SERVER)
        nas_config: dict[str, str] | None = None
        if nas_server:
            nas_config = {
                "server": nas_server,
                "username": self._get_option(CONF_NAS_USERNAME),
                "password": self._get_option(CONF_NAS_PASSWORD),
            }

        data: dict[str, Any] = {
            "missing_movies": [],
            "missing_series": [],
            "missing_anime": [],
            "stats_movies": {},
            "stats_series": {},
            "stats_anime": {},
            "last_scan": dt_util.now().isoformat(),
        }

        try:
            # ---- Movies ----
            if movies_paths:
                scanned = await self.hass.async_add_executor_job(
                    scan_movies, movies_paths, nas_config
                )
                analyzer = MediaAnalyzer(client)
                result: AnalysisResult = await analyzer.analyze_movies(scanned)
                data["missing_movies"] = [m.as_dict() for m in result.missing_movies]
                data["stats_movies"] = {
                    "scanned": result.total_scanned,
                    "collections_found": result.collections_found,
                }

            # ---- Series ----
            if series_paths:
                scanned_s = await self.hass.async_add_executor_job(
                    scan_series, series_paths, nas_config
                )
                analyzer = MediaAnalyzer(client)
                result_s = await analyzer.analyze_series(scanned_s)
                data["missing_series"] = [e.as_dict() for e in result_s.missing_episodes]
                data["stats_series"] = {
                    "scanned": result_s.total_scanned,
                    "series_analyzed": result_s.series_analyzed,
                }

            # ---- Anime ----
            if anime_paths:
                scanned_a = await self.hass.async_add_executor_job(
                    scan_series, anime_paths, nas_config
                )
                analyzer = MediaAnalyzer(client)
                result_a = await analyzer.analyze_series(scanned_a)
                data["missing_anime"] = [e.as_dict() for e in result_a.missing_episodes]
                data["stats_anime"] = {
                    "scanned": result_a.total_scanned,
                    "series_analyzed": result_a.series_analyzed,
                }

        except Exception as exc:
            _LOGGER.exception("Media scan failed")
            raise UpdateFailed(f"Scan failed: {exc}") from exc
        finally:
            client.clear_cache()

        _LOGGER.info(
            "Scan complete: %d missing movies, %d missing episodes, %d missing anime eps",
            len(data["missing_movies"]),
            len(data["missing_series"]),
            len(data["missing_anime"]),
        )
        return data
