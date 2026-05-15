"""Select platform for Parcel Tracker — carrier selection per slot."""
from __future__ import annotations
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, MAX_PARCELS, CARRIERS

_LOGGER = logging.getLogger(__name__)

CARRIER_VALUE_TO_KEY = {v: k for k, v in CARRIERS.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    for i in range(1, MAX_PARCELS + 1):
        initial_key = hass.data[DOMAIN][entry.entry_id]["slots"][i]["carrier"]
        initial_label = CARRIERS.get(initial_key, CARRIERS["auto"])
        entity = ParcelCarrierSelect(entry, i, initial_label)
        hass.data[DOMAIN][entry.entry_id]["select_entities"][i] = entity
        entities.append(entity)
    async_add_entities(entities)


class ParcelCarrierSelect(SelectEntity, RestoreEntity):
    _attr_options = list(CARRIERS.values())

    def __init__(self, entry: ConfigEntry, slot: int, initial: str) -> None:
        self._entry = entry
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_carrier_{slot}"
        self._attr_name = f"Parcel {slot} Carrier"
        self._attr_current_option = initial

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self._attr_options:
            self._attr_current_option = last.state
            carrier_key = CARRIER_VALUE_TO_KEY.get(last.state, "auto")
            self.hass.data[DOMAIN][self._entry.entry_id]["slots"][self._slot]["carrier"] = carrier_key

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        carrier_key = CARRIER_VALUE_TO_KEY.get(option, "auto")
        self.hass.data[DOMAIN][self._entry.entry_id]["slots"][self._slot]["carrier"] = carrier_key
        self.async_write_ha_state()
        coordinator = self.hass.data[DOMAIN][self._entry.entry_id]["coordinator"]
        await coordinator.async_request_refresh()
