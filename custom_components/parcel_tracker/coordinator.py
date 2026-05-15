"""DataUpdateCoordinator for Parcel Tracker."""
from __future__ import annotations
import asyncio
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, MAX_PARCELS
from .scrapers import get_tracking_info

_LOGGER = logging.getLogger(__name__)


class ParcelTrackerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        data = self.entry.options or self.entry.data
        results = {}
        for i in range(1, MAX_PARCELS + 1):
            key = f"parcel_{i}"
            tn = data.get(f"tracking_number_{i}", "").strip()
            carrier = data.get(f"carrier_{i}", "auto")
            friendly = data.get(f"friendly_name_{i}", "") or f"Parcel {i}"
            if not tn:
                results[key] = {
                    "status": "empty", "status_detail": "",
                    "carrier": carrier, "tracking_number": "",
                    "tracking_url": "", "friendly_name": friendly, "slot": i,
                }
                continue
            try:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, get_tracking_info, tn, carrier
                )
            except Exception as exc:
                _LOGGER.warning("Error fetching parcel %d: %s", i, exc)
                info = {
                    "status": "unknown", "status_detail": str(exc),
                    "carrier": carrier, "tracking_number": tn, "tracking_url": "",
                }
            info["friendly_name"] = friendly
            info["slot"] = i
            results[key] = info
        return results
