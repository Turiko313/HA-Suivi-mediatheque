"""Config flow for Media Gap Analyzer."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ANIME_PATHS,
    CONF_LANGUAGE,
    CONF_MOVIES_PATHS,
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


def _validate_paths(raw: str) -> str | None:
    if not raw:
        return None
    for p in raw.split(","):
        p = p.strip()
        if p and not os.path.isdir(p):
            return p
    return None


class MediaGapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate TMDb key
            client = TMDbClient(self.hass, user_input[CONF_TMDB_API_KEY], user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
            if not await client.validate_api_key():
                errors["base"] = "invalid_api_key"
            else:
                # Store API key + language in data, paths + interval in options
                return self.async_create_entry(
                    title="Media Gap Analyzer",
                    data={
                        CONF_TMDB_API_KEY: user_input[CONF_TMDB_API_KEY],
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_MOVIES_PATHS: user_input.get(CONF_MOVIES_PATHS, ""),
                        CONF_SERIES_PATHS: user_input.get(CONF_SERIES_PATHS, ""),
                        CONF_ANIME_PATHS: user_input.get(CONF_ANIME_PATHS, ""),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TMDB_API_KEY): str,
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=720)
                ),
                vol.Optional(CONF_MOVIES_PATHS, default=""): str,
                vol.Optional(CONF_SERIES_PATHS, default=""): str,
                vol.Optional(CONF_ANIME_PATHS, default=""): str,
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

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=720)),
                vol.Optional(
                    CONF_MOVIES_PATHS,
                    default=current.get(CONF_MOVIES_PATHS, ""),
                ): str,
                vol.Optional(
                    CONF_SERIES_PATHS,
                    default=current.get(CONF_SERIES_PATHS, ""),
                ): str,
                vol.Optional(
                    CONF_ANIME_PATHS,
                    default=current.get(CONF_ANIME_PATHS, ""),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
