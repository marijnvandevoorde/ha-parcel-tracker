"""Sensor platform for Parcel Tracker."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MAX_PARCELS, STATUS_ICONS
from .coordinator import ParcelTrackerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ParcelTrackerCoordinator = entry_data["coordinator"]

    entry_data["async_add_sensor_entities"] = async_add_entities
    entry_data["sensor_entities"] = {}

    # Only create sensors for slots that already have a tracking number
    entities = []
    for i in range(1, MAX_PARCELS + 1):
        if entry_data["slots"][i]["tracking"]:
            entity = ParcelSensor(coordinator, i)
            entry_data["sensor_entities"][i] = entity
            entities.append(entity)

    if entities:
        async_add_entities(entities)

    # Sync entities whenever the coordinator refreshes
    entry.async_on_unload(
        coordinator.async_add_listener(
            lambda: hass.async_create_task(
                _sync_sensor_entities(hass, entry.entry_id)
            )
        )
    )


async def _sync_sensor_entities(hass: HomeAssistant, entry_id: str) -> None:
    """Add or remove sensor entities to match current active slots."""
    entry_data = hass.data[DOMAIN].get(entry_id)
    if not entry_data:
        return

    slots = entry_data["slots"]
    current = entry_data["sensor_entities"]
    async_add = entry_data["async_add_sensor_entities"]
    coordinator = entry_data["coordinator"]
    registry = er.async_get(hass)

    active = {i for i in range(1, MAX_PARCELS + 1) if slots[i]["tracking"]}
    existing = set(current.keys())

    # Add sensors for new parcels
    to_add = []
    for slot in sorted(active - existing):
        entity = ParcelSensor(coordinator, slot)
        current[slot] = entity
        to_add.append(entity)
    if to_add:
        async_add(to_add)

    # Remove sensors for deleted parcels
    for slot in existing - active:
        entity = current.pop(slot)
        if entity.entity_id:
            registry.async_remove(entity.entity_id)


class ParcelSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: ParcelTrackerCoordinator, slot: int) -> None:
        super().__init__(coordinator)
        self._slot = slot
        self._attr_unique_id = f"{coordinator.entry.entry_id}_parcel_{slot}"

    @property
    def _data(self) -> dict:
        if not self.coordinator.data:
            return {}
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
        # Stay available as long as the slot holds a parcel — an "unknown"
        # status (carrier returned no data yet) must not drop the entity's
        # attributes, or the tracking_url link disappears from cards.
        return bool(self._data.get("tracking_number")) and self._data.get(
            "status", "empty"
        ) != "empty"

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
