"""WebSocket API commands for the Parcel Tracker panel."""
from __future__ import annotations
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
import voluptuous as vol
from .const import DOMAIN, MAX_PARCELS, CARRIERS

_VALID_SLOTS = range(1, MAX_PARCELS + 1)


def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_list_parcels)
    websocket_api.async_register_command(hass, ws_set_parcel)
    websocket_api.async_register_command(hass, ws_refresh)


@callback
@websocket_api.websocket_command({vol.Required("type"): "parcel_tracker/list"})
def ws_list_parcels(hass: HomeAssistant, connection, msg: dict) -> None:
    result = []
    for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
        if not isinstance(entry_data, dict) or "slots" not in entry_data:
            continue
        slots = entry_data["slots"]
        coordinator = entry_data.get("coordinator")
        coord_data = coordinator.data if coordinator and coordinator.data else {}
        parcels = []
        for i in _VALID_SLOTS:
            slot = slots.get(i, {})
            status_data = coord_data.get(f"parcel_{i}", {})
            parcels.append({
                "slot": i,
                "tracking": slot.get("tracking", ""),
                "carrier": slot.get("carrier", "auto"),
                "friendly_name": slot.get("friendly_name", f"Parcel {i}"),
                "status": status_data.get("status", "empty"),
                "status_detail": status_data.get("status_detail", ""),
                "tracking_url": status_data.get("tracking_url", ""),
            })
        last_checked = coordinator.last_checked.isoformat() if coordinator and coordinator.last_checked else None
        result.append({"entry_id": entry_id, "parcels": parcels, "last_checked": last_checked})
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({
    vol.Required("type"): "parcel_tracker/refresh",
    vol.Required("entry_id"): str,
})
@websocket_api.async_response
async def ws_refresh(hass: HomeAssistant, connection, msg: dict) -> None:
    entry_id = msg["entry_id"]
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if not isinstance(entry_data, dict) or "coordinator" not in entry_data:
        connection.send_error(msg["id"], "not_found", "Entry not found")
        return
    coordinator = entry_data.get("coordinator")
    if coordinator:
        await coordinator.async_request_refresh()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "parcel_tracker/set_parcel",
    vol.Required("entry_id"): str,
    vol.Required("slot"): int,
    vol.Required("tracking"): str,
    vol.Required("carrier"): str,
    vol.Optional("friendly_name"): str,
})
@websocket_api.async_response
async def ws_set_parcel(hass: HomeAssistant, connection, msg: dict) -> None:
    entry_id = msg["entry_id"]
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if not isinstance(entry_data, dict) or "slots" not in entry_data:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    slot = msg["slot"]
    if slot not in _VALID_SLOTS:
        connection.send_error(msg["id"], "invalid_slot", f"Slot must be between 1 and {MAX_PARCELS}")
        return

    slots = entry_data["slots"]
    if slot not in slots:
        connection.send_error(msg["id"], "invalid_slot", "Slot does not exist")
        return

    slots[slot]["tracking"] = msg["tracking"].strip()
    slots[slot]["carrier"] = msg["carrier"]
    if "friendly_name" in msg:
        slots[slot]["friendly_name"] = msg["friendly_name"]

    store = entry_data.get("store")
    if store:
        await store.async_save({str(i): s for i, s in slots.items()})

    coordinator = entry_data.get("coordinator")
    if coordinator:
        await coordinator.async_request_refresh()

    connection.send_result(msg["id"], {"success": True})
