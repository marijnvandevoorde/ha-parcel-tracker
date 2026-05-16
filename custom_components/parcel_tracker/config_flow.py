"""Config flow for Parcel Tracker."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_DHL_API_KEY, CONF_PKGE_API_KEY


class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            options = {
                CONF_DHL_API_KEY: (user_input.get(CONF_DHL_API_KEY) or "").strip(),
                CONF_PKGE_API_KEY: (user_input.get(CONF_PKGE_API_KEY) or "").strip(),
            }
            return self.async_create_entry(
                title="Parcel Tracker",
                data={},
                options=options,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DHL_API_KEY): str,
                    vol.Optional(CONF_PKGE_API_KEY): str,
                }
            ),
            description_placeholders={
                "dhl_url": "developer.dhl.com",
                "pkge_url": "business.pkge.net",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ParcelTrackerOptionsFlow(config_entry)


class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    """Options flow for updating API keys after installation."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            cleaned = {
                CONF_DHL_API_KEY: (user_input.get(CONF_DHL_API_KEY) or "").strip(),
                CONF_PKGE_API_KEY: (user_input.get(CONF_PKGE_API_KEY) or "").strip(),
            }
            return self.async_create_entry(title="", data=cleaned)

        current = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DHL_API_KEY,
                        description={
                            "suggested_value": current.get(CONF_DHL_API_KEY, "")
                        },
                    ): str,
                    vol.Optional(
                        CONF_PKGE_API_KEY,
                        description={
                            "suggested_value": current.get(CONF_PKGE_API_KEY, "")
                        },
                    ): str,
                }
            ),
            description_placeholders={
                "dhl_url": "developer.dhl.com",
                "pkge_url": "business.pkge.net",
            },
        )
