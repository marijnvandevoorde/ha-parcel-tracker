"""Parcel Tracker integration for Home Assistant."""
from __future__ import annotations
import logging
from pathlib import Path
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.helpers.storage import Store
from .const import DOMAIN, MAX_PARCELS
from .coordinator import ParcelTrackerCoordinator
from . import ws_api

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
STORAGE_VERSION = 1
PANEL_URL = "parcel-tracker"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Load persisted slot data, fall back to config entry data
    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    stored = await store.async_load() or {}
    config_data = entry.options or entry.data

    slots = {}
    for i in range(1, MAX_PARCELS + 1):
        saved = stored.get(str(i), {})
        slots[i] = {
            "tracking": saved.get("tracking") or config_data.get(f"tracking_number_{i}", "") or "",
            "carrier": saved.get("carrier") or config_data.get(f"carrier_{i}", "auto"),
            "friendly_name": saved.get("friendly_name") or config_data.get(f"friendly_name_{i}", "") or f"Parcel {i}",
        }

    coordinator = ParcelTrackerCoordinator(hass, entry)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "slots": slots,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register WebSocket API and frontend panel once
    if not hass.data[DOMAIN].get("_panel_registered"):
        hass.data[DOMAIN]["_panel_registered"] = True
        ws_api.async_register(hass)

        hass.http.register_static_path(
            f"/{DOMAIN}_frontend",
            str(Path(__file__).parent / "frontend"),
            cache_headers=False,
        )
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Parcel Tracker",
            sidebar_icon="mdi:package-variant",
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": "parcel-tracker-panel",
                    "js_url": f"/{DOMAIN}_frontend/parcel-tracker-panel.js",
                }
            },
            require_admin=False,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Remove panel when no entries remain
    remaining = [k for k in hass.data[DOMAIN] if not k.startswith("_")]
    if not remaining:
        async_remove_panel(hass, PANEL_URL)
        hass.data[DOMAIN].pop("_panel_registered", None)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
