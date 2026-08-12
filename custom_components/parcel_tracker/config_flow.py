"""Config flow for Parcel Tracker."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_POSTAL_CODE, CONF_DHL_API_KEY, CONF_17TRACK_API_KEY

DESCRIPTION_PLACEHOLDERS = {
    "dhl_url": "developer.dhl.com",
    "seventeentrack_url": "api.17track.net",
}


def _clean(user_input: dict) -> dict:
    return {
        CONF_DHL_API_KEY: (user_input.get(CONF_DHL_API_KEY) or "").strip(),
        CONF_17TRACK_API_KEY: (user_input.get(CONF_17TRACK_API_KEY) or "").strip(),
        CONF_POSTAL_CODE: (user_input.get(CONF_POSTAL_CODE) or "").strip(),
    }


class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Store settings in data (options= is not supported in config flow)
            return self.async_create_entry(
                title="Parcel Tracker", data=_clean(user_input)
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DHL_API_KEY): str,
                    vol.Optional(CONF_17TRACK_API_KEY): str,
                    vol.Optional(CONF_POSTAL_CODE): str,
                }
            ),
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ParcelTrackerOptionsFlow()


class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    """Options flow for updating settings after installation."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=_clean(user_input))

        current = self.config_entry.options
        data = self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DHL_API_KEY,
                        description={
                            "suggested_value": current.get(CONF_DHL_API_KEY)
                            or data.get(CONF_DHL_API_KEY, "")
                        },
                    ): str,
                    vol.Optional(
                        CONF_17TRACK_API_KEY,
                        description={
                            "suggested_value": current.get(CONF_17TRACK_API_KEY)
                            or data.get(CONF_17TRACK_API_KEY, "")
                        },
                    ): str,
                    vol.Optional(
                        CONF_POSTAL_CODE,
                        description={
                            "suggested_value": current.get(CONF_POSTAL_CODE)
                            or data.get(CONF_POSTAL_CODE, "")
                        },
                    ): str,
                }
            ),
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )
