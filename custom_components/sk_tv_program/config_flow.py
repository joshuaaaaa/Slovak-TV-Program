"""Config flow for Slovak TV Program integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, AVAILABLE_CHANNELS

_LOGGER = logging.getLogger(__name__)


class SkTVProgramConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Slovak TV Program."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate and create entry
            await self.async_set_unique_id(f"sk_tv_program_default")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Slovak TV Program",
                data=user_input,
            )

        # Build multi-select options for channels
        channel_options = {
            channel_id: channel_name 
            for channel_id, channel_name in AVAILABLE_CHANNELS.items()
        }

        data_schema = vol.Schema(
            {
                vol.Required("channels", default=list(AVAILABLE_CHANNELS.keys())): cv.multi_select(channel_options),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SkTVProgramOptionsFlow(config_entry)


class SkTVProgramOptionsFlow(config_entries.OptionsFlow):
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
