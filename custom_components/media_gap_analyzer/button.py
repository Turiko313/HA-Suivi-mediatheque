"""Button platform for Suivi Médiathèque."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MediaGapCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator: MediaGapCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScanNowButton(coordinator, entry)])


class ScanNowButton(ButtonEntity):
    """Button to trigger a manual media scan."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MediaGapCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_scan_now"
        self._attr_name = "Lancer le scan"
        self._attr_icon = "mdi:magnify-scan"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._coordinator.async_request_refresh()
