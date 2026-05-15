"""Parcel Tracker integration for Home Assistant."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from .const import DOMAIN, MAX_PARCELS
from .coordinator import ParcelTrackerCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.TEXT, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    data = entry.options or entry.data

    slots = {
        i: {
            "tracking": data.get(f"tracking_number_{i}", "") or "",
            "carrier": data.get(f"carrier_{i}", "auto"),
            "friendly_name": data.get(f"friendly_name_{i}", "") or f"Parcel {i}",
        }
        for i in range(1, MAX_PARCELS + 1)
    }

    coordinator = ParcelTrackerCoordinator(hass, entry)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "slots": slots,
        "text_entities": {},
        "select_entities": {},
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
