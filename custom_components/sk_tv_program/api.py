"""API client for Slovak TV Program."""
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element  # ✅ přidáno – pouze pro typovou anotaci

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import XMLTV_API_URL, API_TIMEOUT, AVAILABLE_CHANNELS, DEFAULT_DAYS_AHEAD

_LOGGER = logging.getLogger(__name__)


class SkTVProgramAPI:
    """API client for Slovak TV Program."""

    def __init__(self, hass: HomeAssistant, channels: List[str]):
        """Initialize the API client."""
        self.hass = hass
        self.channels = channels or list(AVAILABLE_CHANNELS.keys())
        self.session = async_get_clientsession(hass)
        
    async def async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            all_data = {}
            xmltv_data = await self._fetch_xmltv()
            for channel_id in self.channels:
                channel_programs = self._filter_channel_programs(xmltv_data, channel_id)
                all_data[channel_id] = channel_programs
            return all_data
        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err)
            raise
    
    async def _fetch_xmltv(self) -> Element:
        """Fetch XMLTV data from API."""
        try:
            async with self.session.get(XMLTV_API_URL, timeout=API_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    return root
                else:
                    _LOGGER.warning("Failed to fetch XMLTV: HTTP %s", response.status)
                    return None
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching XMLTV data")
            return None
        except Exception as err:
            _LOGGER.error("Error fetching XMLTV: %s", err)
            return None
    
    def _filter_channel_programs(self, xmltv_root: Element, channel_id: str) -> List[Dict[str, Any]]:
        """Filter and parse programs for specific channel."""
        programs = []
        if xmltv_root is None:
            return programs

        now = datetime.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)
        
        channel_map = {
            "rtvs1": ["Jednotka", "RTVS 1", "RTVS1"],
            "rtvs2": ["Dvojka", "RTVS 2", "RTVS2"],
            "rtvs24": ["RTVS 24", ":24", "RTVS24"],
        }
