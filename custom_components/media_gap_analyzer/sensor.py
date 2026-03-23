"""Sensor platform for Suivi Médiathèque."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MediaGapCoordinator

MAX_ATTR_ITEMS = 100  # cap attribute list to avoid huge states


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MediaGapCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            MissingMoviesSensor(coordinator, entry),
            MissingSeriesSensor(coordinator, entry),
            MissingAnimeSensor(coordinator, entry),
            MissingCartoonsSensor(coordinator, entry),
            LastScanSensor(coordinator, entry),
        ]
    )


class _BaseSensor(CoordinatorEntity[MediaGapCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MediaGapCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon


class MissingMoviesSensor(_BaseSensor):
    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "missing_movies", "Films manquants", "mdi:movie-open-remove")

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return len(self.coordinator.data.get("missing_movies", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        items = self.coordinator.data.get("missing_movies", [])
        stats = self.coordinator.data.get("stats_movies", {})
        # Group by collection for readability
        collections: dict[str, list[str]] = {}
        for m in items[:MAX_ATTR_ITEMS]:
            coll = m.get("collection", "Unknown")
            title = m.get("title", "?")
            year = m.get("year")
            label = f"{title} ({year})" if year else title
            collections.setdefault(coll, []).append(label)
        return {
            "missing_by_collection": collections,
            "total_missing": len(items),
            **stats,
        }


class MissingSeriesSensor(_BaseSensor):
    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "missing_series", "Episodes manquants (Series)", "mdi:television-off")

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return len(self.coordinator.data.get("missing_series", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        items = self.coordinator.data.get("missing_series", [])
        stats = self.coordinator.data.get("stats_series", {})
        grouped: dict[str, dict[str, list[int]]] = {}
        for ep in items[:MAX_ATTR_ITEMS]:
            show = ep.get("series", "?")
            season_key = f"S{ep.get('season', 0):02d}"
            grouped.setdefault(show, {}).setdefault(season_key, []).append(ep.get("episode", 0))
        return {
            "missing_by_series": grouped,
            "total_missing": len(items),
            **stats,
        }


class MissingAnimeSensor(_BaseSensor):
    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "missing_anime", "Episodes manquants (Anime)", "mdi:cards-playing-spade")

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return len(self.coordinator.data.get("missing_anime", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        items = self.coordinator.data.get("missing_anime", [])
        stats = self.coordinator.data.get("stats_anime", {})
        grouped: dict[str, dict[str, list[int]]] = {}
        for ep in items[:MAX_ATTR_ITEMS]:
            show = ep.get("series", "?")
            season_key = f"S{ep.get('season', 0):02d}"
            grouped.setdefault(show, {}).setdefault(season_key, []).append(ep.get("episode", 0))
        return {
            "missing_by_series": grouped,
            "total_missing": len(items),
            **stats,
        }


class MissingCartoonsSensor(_BaseSensor):
    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "missing_cartoons", "Episodes manquants (Dessins anim\u00e9s)", "mdi:teddy-bear")

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return len(self.coordinator.data.get("missing_cartoons", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        items = self.coordinator.data.get("missing_cartoons", [])
        stats = self.coordinator.data.get("stats_cartoons", {})
        grouped: dict[str, dict[str, list[int]]] = {}
        for ep in items[:MAX_ATTR_ITEMS]:
            show = ep.get("series", "?")
            season_key = f"S{ep.get('season', 0):02d}"
            grouped.setdefault(show, {}).setdefault(season_key, []).append(ep.get("episode", 0))
        return {
            "missing_by_series": grouped,
            "total_missing": len(items),
            **stats,
        }


class LastScanSensor(_BaseSensor):
    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "last_scan", "Dernier scan mediatheque", "mdi:clock-check-outline")
        self._attr_device_class = "timestamp"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data:
            return self.coordinator.data.get("last_scan")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return {
            "movies": self.coordinator.data.get("stats_movies", {}),
            "series": self.coordinator.data.get("stats_series", {}),
            "anime": self.coordinator.data.get("stats_anime", {}),
            "cartoons": self.coordinator.data.get("stats_cartoons", {}),
        }
