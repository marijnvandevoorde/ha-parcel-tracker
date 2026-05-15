"""Config flow for Parcel Tracker."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CARRIERS, MAX_PARCELS

CARRIER_OPTIONS = [
    selector.SelectOptionDict(value=k, label=v) for k, v in CARRIERS.items()
]


def _parcel_schema(data: dict, start: int = 1, end: int = 5) -> vol.Schema:
    fields = {}
    for i in range(start, end + 1):
        fields[vol.Optional(f"friendly_name_{i}", default=data.get(f"friendly_name_{i}", f"Parcel {i}"))] = str
        fields[vol.Optional(f"tracking_number_{i}", default=data.get(f"tracking_number_{i}", ""))] = str
        fields[vol.Optional(f"carrier_{i}", default=data.get(f"carrier_{i}", "auto"))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=CARRIER_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN)
        )
    return vol.Schema(fields)


class ParcelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_parcels_6_10()
        return self.async_show_form(
            step_id="user",
            data_schema=_parcel_schema(self._data, 1, 5),
            description_placeholders={"parcels": "1-5"},
        )

    async def async_step_parcels_6_10(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Parcel Tracker", data=self._data)
        return self.async_show_form(
            step_id="parcels_6_10",
            data_schema=_parcel_schema(self._data, 6, 10),
            description_placeholders={"parcels": "6-10"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ParcelTrackerOptionsFlow(config_entry)


class ParcelTrackerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry
        self._data = dict(config_entry.options or config_entry.data)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_options_6_10()
        return self.async_show_form(
            step_id="init",
            data_schema=_parcel_schema(self._data, 1, 5),
        )

    async def async_step_options_6_10(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return self.async_show_form(
            step_id="options_6_10",
            data_schema=_parcel_schema(self._data, 6, 10),
        )
