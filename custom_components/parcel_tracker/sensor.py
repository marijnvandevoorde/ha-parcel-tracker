"""Sensor platform for Parcel Tracker."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MAX_PARCELS, STATUS_ICONS
from .coordinator import ParcelTrackerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ParcelTrackerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ParcelSensor(coordinator, i) for i in range(1, MAX_PARCELS + 1)
    )


class ParcelSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: ParcelTrackerCoordinator, slot: int) -> None:
        super().__init__(coordinator)
        self._slot = slot
        self._attr_unique_id = f"{coordinator.entry.entry_id}_parcel_{slot}"

    @property
    def _data(self) -> dict:
        return self.coordinator.data.get(f"parcel_{self._slot}", {})

    @property
    def name(self) -> str:
        return self._data.get("friendly_name", f"Parcel {self._slot}")

    @property
    def state(self) -> str:
        return self._data.get("status", "unknown")

    @property
    def icon(self) -> str:
        return STATUS_ICONS.get(self.state, "mdi:package-variant")

    @property
    def available(self) -> bool:
        return self._data.get("status", "empty") != "empty"

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data
        return {
            "tracking_number": d.get("tracking_number", ""),
            "carrier": d.get("carrier", ""),
            "status_detail": d.get("status_detail", ""),
            "tracking_url": d.get("tracking_url", ""),
            "slot": self._slot,
        }
