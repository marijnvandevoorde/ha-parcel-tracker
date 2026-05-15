"""Config flow for Parcel Tracker."""
from __future__ import annotations
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN


class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Parcel Tracker", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ParcelTrackerOptionsFlow(config_entry)


class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        return self.async_abort(reason="use_panel")
