"""DataUpdateCoordinator for Parcel Tracker."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, MAX_PARCELS, CONF_DHL_API_KEY, CONF_PKGE_API_KEY
from .scrapers import get_tracking_info, TrackerConfig

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
        self.last_checked: datetime | None = None

    def _get_config(self) -> TrackerConfig:
        """Build a TrackerConfig from the current config entry.

        Keys set via the options flow (entry.options) take precedence over
        keys stored during initial installation (entry.data).
        """
        options = self.entry.options or {}
        data = self.entry.data or {}
        return TrackerConfig(
            dhl_api_key=options.get(CONF_DHL_API_KEY) or data.get(CONF_DHL_API_KEY, ""),
            pkge_api_key=options.get(CONF_PKGE_API_KEY) or data.get(CONF_PKGE_API_KEY, ""),
        )

    async def _async_update_data(self) -> dict:
        slots = self.hass.data[DOMAIN][self.entry.entry_id]["slots"]
        config = self._get_config()
        results = {}
        for i in range(1, MAX_PARCELS + 1):
            key = f"parcel_{i}"
            slot = slots[i]
            tn = str(slot.get("tracking") or "").strip()
            carrier = slot["carrier"]
            friendly = slot["friendly_name"]
            if not tn:
                results[key] = {
                    "status": "empty", "status_detail": "",
                    "carrier": carrier, "tracking_number": "",
                    "tracking_url": "", "friendly_name": friendly, "slot": i,
                }
                continue
            try:
                info = await self.hass.async_add_executor_job(
                    get_tracking_info, tn, carrier, config
                )
            except Exception as exc:
                _LOGGER.warning("Error fetching parcel %d (%s): %s", i, tn, exc)
                info = {
                    "status": "unknown", "status_detail": str(exc),
                    "carrier": carrier, "tracking_number": tn, "tracking_url": "",
                }
            _LOGGER.debug(
                "Parcel %d (%s) carrier=%s status=%s detail=%s",
                i, tn, info.get("carrier"), info.get("status"), info.get("status_detail"),
            )
            info["friendly_name"] = friendly
            info["slot"] = i
            results[key] = info
        self.last_checked = datetime.now(timezone.utc)
        return results
