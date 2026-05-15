"""Parcel Tracker integration for Home Assistant."""
from __future__ import annotations
import logging
from pathlib import Path
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from .const import DOMAIN, MAX_PARCELS, CARRIERS, VERSION
from .coordinator import ParcelTrackerCoordinator
from . import ws_api

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
STORAGE_VERSION = 1
PANEL_URL = "parcel-tracker"

SERVICE_ADD_PARCEL = "add_parcel"
SERVICE_REMOVE_PARCEL = "remove_parcel"

ADD_PARCEL_SCHEMA = vol.Schema({
    vol.Required("tracking_number"): cv.string,
    vol.Optional("carrier", default="auto"): vol.In(list(CARRIERS.keys())),
    vol.Optional("friendly_name", default=""): cv.string,
})

REMOVE_PARCEL_SCHEMA = vol.Schema({
    vol.Required("tracking_number"): cv.string,
})


async def _save_slots(hass: HomeAssistant, entry_id: str) -> None:
    entry_data = hass.data[DOMAIN][entry_id]
    store = entry_data.get("store")
    if store:
        await store.async_save({str(i): s for i, s in entry_data["slots"].items()})
    coordinator = entry_data.get("coordinator")
    if coordinator:
        await coordinator.async_request_refresh()


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

    # Register WebSocket API, panel and services once
    if not hass.data[DOMAIN].get("_panel_registered"):
        hass.data[DOMAIN]["_panel_registered"] = True
        ws_api.async_register(hass)

        await hass.http.async_register_static_paths([
            StaticPathConfig(
                f"/{DOMAIN}_frontend",
                str(Path(__file__).parent / "frontend"),
                cache_headers=False,
            )
        ])
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Parcel Tracker",
            sidebar_icon="mdi:package-variant",
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": "parcel-tracker-panel",
                    "js_url": f"/{DOMAIN}_frontend/parcel-tracker-panel.js?v={VERSION}",
                }
            },
            require_admin=False,
        )

        async def handle_add_parcel(call: ServiceCall) -> None:
            tracking = call.data["tracking_number"].strip()
            carrier = call.data.get("carrier", "auto")
            name = call.data.get("friendly_name", "").strip()

            # Find the first entry_id with a free slot
            for eid, entry_data in hass.data[DOMAIN].items():
                if not isinstance(entry_data, dict) or "slots" not in entry_data:
                    continue
                slots = entry_data["slots"]
                # Check if tracking number already exists
                for slot in slots.values():
                    if slot["tracking"] == tracking:
                        _LOGGER.warning("Tracking number %s already exists", tracking)
                        return
                # Find first empty slot
                for i in range(1, MAX_PARCELS + 1):
                    if not slots[i]["tracking"]:
                        slots[i]["tracking"] = tracking
                        slots[i]["carrier"] = carrier
                        slots[i]["friendly_name"] = name or f"Parcel {i}"
                        await _save_slots(hass, eid)
                        return
                _LOGGER.warning("No free slots available to add parcel %s", tracking)
                return

        async def handle_remove_parcel(call: ServiceCall) -> None:
            tracking = call.data["tracking_number"].strip()

            for eid, entry_data in hass.data[DOMAIN].items():
                if not isinstance(entry_data, dict) or "slots" not in entry_data:
                    continue
                slots = entry_data["slots"]
                for i in range(1, MAX_PARCELS + 1):
                    if slots[i]["tracking"] == tracking:
                        slots[i]["tracking"] = ""
                        slots[i]["carrier"] = "auto"
                        slots[i]["friendly_name"] = f"Parcel {i}"
                        await _save_slots(hass, eid)
                        return
                _LOGGER.warning("Tracking number %s not found", tracking)

        hass.services.async_register(
            DOMAIN, SERVICE_ADD_PARCEL, handle_add_parcel, schema=ADD_PARCEL_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, SERVICE_REMOVE_PARCEL, handle_remove_parcel, schema=REMOVE_PARCEL_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    remaining = [k for k in hass.data[DOMAIN] if not k.startswith("_")]
    if not remaining:
        async_remove_panel(hass, PANEL_URL)
        hass.services.async_remove(DOMAIN, SERVICE_ADD_PARCEL)
        hass.services.async_remove(DOMAIN, SERVICE_REMOVE_PARCEL)
        hass.data[DOMAIN].pop("_panel_registered", None)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
