"""Slovak TV Program Integration for Home Assistant."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PLATFORMS
from .api import SkTVProgramAPI

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=6)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Slovak TV Program component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Slovak TV Program from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    try:
        channels = entry.data.get("channels", [])

        # Create a coordinator for each channel
        coordinators = {}

        for channel_id in channels:
            api = SkTVProgramAPI(
                hass=hass,
                channels=[channel_id]  # Only this channel
            )

            async def async_update_data(channel=channel_id, api_instance=api):
                """Fetch data with error handling for a specific channel."""
                try:
                    _LOGGER.info("Fetching data for channel %s", channel)
                    data = await api_instance.async_update_channel_data(channel)
                    if not data:
                        _LOGGER.warning("No data received from API for channel %s", channel)
                    else:
                        _LOGGER.info("Successfully fetched %d programs for channel %s", len(data), channel)
                    return data
                except Exception as err:
                    _LOGGER.error("Error fetching data for channel %s: %s", channel, err, exc_info=True)
                    raise UpdateFailed(f"Error fetching data for {channel}: {err}") from err

            coordinator = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name=f"{DOMAIN}_{channel_id}",
                update_method=async_update_data,
                update_interval=SCAN_INTERVAL,
            )

            # První refresh s timeout protection
            try:
                await coordinator.async_config_entry_first_refresh()
            except Exception as err:
                _LOGGER.error("Failed to fetch initial data for %s: %s", channel_id, err)
                # Continue with other channels even if one fails
                continue

            coordinators[channel_id] = {
                "coordinator": coordinator,
                "api": api,
            }

        if not coordinators:
            raise ConfigEntryNotReady("Failed to fetch initial data for all channels")

        hass.data[DOMAIN][entry.entry_id] = coordinators

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("Slovak TV Program integration loaded successfully with %d channels", len(coordinators))
        return True

    except ConfigEntryNotReady:
        raise
    except Exception as err:
        _LOGGER.error("Unexpected error setting up Slovak TV Program: %s", err, exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("Slovak TV Program integration unloaded successfully")
        
        return unload_ok
        
    except Exception as err:
        _LOGGER.error("Error unloading Slovak TV Program: %s", err, exc_info=True)
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
