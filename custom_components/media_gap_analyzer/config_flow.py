"""Config flow for Suivi Médiathèque."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_ANIME_PATHS,
    CONF_CARTOONS_PATHS,
    CONF_LANGUAGE,
    CONF_MOVIES_PATHS,
    CONF_NAS_PASSWORD,
    CONF_NAS_SERVER,
    CONF_NAS_USERNAME,
    CONF_SCAN_INTERVAL,
    CONF_SERIES_PATHS,
    CONF_TMDB_API_KEY,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .tmdb_client import TMDbClient

_LOGGER = logging.getLogger(__name__)

LANGUAGES = {
    "fr": "Francais",
    "en": "English",
    "de": "Deutsch",
    "es": "Espanol",
    "it": "Italiano",
    "pt": "Portugues",
    "ja": "Japanese",
    "ko": "Korean",
}


def _detect_media_dirs() -> list[str]:
    """Scan /media and /share for directories (2 levels deep)."""
    dirs: list[str] = []
    for root in ("/media", "/share"):
        if not os.path.isdir(root):
            continue
        try:
            for entry in sorted(os.listdir(root)):
                full = os.path.join(root, entry)
                if not os.path.isdir(full):
                    continue
                dirs.append(full)
                try:
                    for sub in sorted(os.listdir(full)):
                        sub_full = os.path.join(full, sub)
                        if os.path.isdir(sub_full):
                            dirs.append(sub_full)
                except PermissionError:
                    pass
        except PermissionError:
            pass
    return dirs


def _path_selector(detected: list[str]) -> SelectSelector:
    """Build a path selector with detected directories + custom value support."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[{"value": d, "label": d} for d in detected],
            multiple=True,
            custom_value=True,
            mode="dropdown",
        )
    )


class MediaGapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input.get(CONF_TMDB_API_KEY, "").strip()
            # Validate TMDb key only if provided
            if api_key:
                client = TMDbClient(
                    self.hass,
                    api_key,
                    user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                )
                if not await client.validate_api_key():
                    errors["base"] = "invalid_api_key"

            if not errors:
                return self.async_create_entry(
                    title="Suivi Médiathèque",
                    data={
                        CONF_TMDB_API_KEY: api_key,
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_NAS_SERVER: user_input.get(CONF_NAS_SERVER, ""),
                        CONF_NAS_USERNAME: user_input.get(CONF_NAS_USERNAME, ""),
                        CONF_NAS_PASSWORD: user_input.get(CONF_NAS_PASSWORD, ""),
                        CONF_MOVIES_PATHS: user_input.get(CONF_MOVIES_PATHS, []),
                        CONF_SERIES_PATHS: user_input.get(CONF_SERIES_PATHS, []),
                        CONF_ANIME_PATHS: user_input.get(CONF_ANIME_PATHS, []),
                        CONF_CARTOONS_PATHS: user_input.get(CONF_CARTOONS_PATHS, []),
                    },
                )

        detected = await self.hass.async_add_executor_job(_detect_media_dirs)
        selector = _path_selector(detected)

        schema = vol.Schema(
            {
                vol.Optional(CONF_TMDB_API_KEY, default=""): str,
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=720)
                ),
                vol.Optional(CONF_NAS_SERVER, default=""): str,
                vol.Optional(CONF_NAS_USERNAME, default=""): str,
                vol.Optional(CONF_NAS_PASSWORD, default=""): str,
                vol.Optional(CONF_MOVIES_PATHS, default=[]): selector,
                vol.Optional(CONF_SERIES_PATHS, default=[]): selector,
                vol.Optional(CONF_ANIME_PATHS, default=[]): selector,
                vol.Optional(CONF_CARTOONS_PATHS, default=[]): selector,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MediaGapOptionsFlow(config_entry)


class MediaGapOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options

        detected = await self.hass.async_add_executor_job(_detect_media_dirs)
        selector = _path_selector(detected)

        def _as_list(key: str) -> list[str]:
            """Get current paths as list (handles old CSV string format)."""
            val = current.get(key, [])
            if isinstance(val, str):
                return [p.strip() for p in val.split(",") if p.strip()]
            return val

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=720)),
                vol.Optional(
                    CONF_NAS_SERVER,
                    default=current.get(CONF_NAS_SERVER, ""),
                ): str,
                vol.Optional(
                    CONF_NAS_USERNAME,
                    default=current.get(CONF_NAS_USERNAME, ""),
                ): str,
                vol.Optional(
                    CONF_NAS_PASSWORD,
                    default=current.get(CONF_NAS_PASSWORD, ""),
                ): str,
                vol.Optional(
                    CONF_MOVIES_PATHS,
                    default=_as_list(CONF_MOVIES_PATHS),
                ): selector,
                vol.Optional(
                    CONF_SERIES_PATHS,
                    default=_as_list(CONF_SERIES_PATHS),
                ): selector,
                vol.Optional(
                    CONF_ANIME_PATHS,
                    default=_as_list(CONF_ANIME_PATHS),
                ): selector,
                vol.Optional(
                    CONF_CARTOONS_PATHS,
                    default=_as_list(CONF_CARTOONS_PATHS),
                ): selector,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
