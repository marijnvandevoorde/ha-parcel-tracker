"""WebSocket API commands for the Parcel Tracker panel."""
from __future__ import annotations
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
import voluptuous as vol
from .const import DOMAIN, MAX_PARCELS, CARRIERS


def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_list_parcels)
    websocket_api.async_register_command(hass, ws_set_parcel)


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
        for i in range(1, MAX_PARCELS + 1):
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
        result.append({"entry_id": entry_id, "parcels": parcels})
    connection.send_result(msg["id"], result)


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
    if entry_id not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    entry_data = hass.data[DOMAIN][entry_id]
    slot = msg["slot"]
    entry_data["slots"][slot]["tracking"] = msg["tracking"]
    entry_data["slots"][slot]["carrier"] = msg["carrier"]
    if "friendly_name" in msg:
        entry_data["slots"][slot]["friendly_name"] = msg["friendly_name"]

    store = entry_data.get("store")
    if store:
        await store.async_save({str(i): s for i, s in entry_data["slots"].items()})

    coordinator = entry_data.get("coordinator")
    if coordinator:
        await coordinator.async_request_refresh()

    connection.send_result(msg["id"], {"success": True})
