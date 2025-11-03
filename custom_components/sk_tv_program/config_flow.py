"""Config flow for Slovak TV Program integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, AVAILABLE_CHANNELS

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Slovak TV Program."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Slovak TV Program",
                data=user_input,
            )

        channel_options = {
            channel_id: channel_name 
            for channel_id, channel_name in AVAILABLE_CHANNELS.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "channels",
                        default=list(AVAILABLE_CHANNELS.keys())
                    ): cv.multi_select(channel_options),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Slovak TV Program."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        channel_options = {
            channel_id: channel_name 
            for channel_id, channel_name in AVAILABLE_CHANNELS.items()
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "channels",
                        default=self.config_entry.data.get("channels", list(AVAILABLE_CHANNELS.keys())),
                    ): cv.multi_select(channel_options),
                }
            ),
        )
