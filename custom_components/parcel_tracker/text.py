"""Text platform for Parcel Tracker — editable tracking numbers."""
from __future__ import annotations
import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, MAX_PARCELS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    for i in range(1, MAX_PARCELS + 1):
        initial = hass.data[DOMAIN][entry.entry_id]["slots"][i]["tracking"]
        entity = ParcelTrackingText(entry, i, initial)
        hass.data[DOMAIN][entry.entry_id]["text_entities"][i] = entity
        entities.append(entity)
    async_add_entities(entities)


class ParcelTrackingText(TextEntity, RestoreEntity):
    _attr_native_min = 0
    _attr_native_max = 100

    def __init__(self, entry: ConfigEntry, slot: int, initial: str) -> None:
        self._entry = entry
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_tracking_{slot}"
        self._attr_name = f"Parcel {slot} Tracking Number"
        self._attr_native_value = initial

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in (None, "unknown", "unavailable"):
            self._attr_native_value = last.state
            self.hass.data[DOMAIN][self._entry.entry_id]["slots"][self._slot]["tracking"] = last.state

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id]["slots"][self._slot]["tracking"] = value
        self.async_write_ha_state()
        coordinator = self.hass.data[DOMAIN][self._entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
