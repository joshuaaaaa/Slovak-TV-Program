"""API client for Slovak TV Program."""
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element

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
            if xmltv_data is None:
                _LOGGER.warning("XMLTV data is empty")
                return all_data

            for channel_id in self.channels:
                channel_programs = self._filter_channel_programs(xmltv_data, channel_id)
                all_data[channel_id] = channel_programs

            _LOGGER.debug("Fetched TV program for %d channels", len(all_data))
            return all_data

        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err)
            raise

    async def _fetch_xmltv(self) -> Optional[Element]:
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
        programs: List[Dict[str, Any]] = []
        if xmltv_root is None:
            return programs

        now = datetime.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)

        channel_map = {
            "rtvs1": ["Jednotka", "RTVS 1", "RTVS1"],
            "rtvs2": ["Dvojka", "RTVS 2", "RTVS2"],
            "rtvs24": ["RTVS 24", ":24", "RTVS24"],
            "markiza": ["Markíza", "Markiza"],
            "joj": ["JOJ"],
            "jojplus": ["JOJ Plus", "Plus"],
            "joj24": ["JOJ 24"],
            "nova": ["Nova International", "Nova Intl"],
            "prima": ["Prima Plus"],
        }

        channel_names = channel_map.get(channel_id, [channel_id])

        for programme in xmltv_root.findall("programme"):
            channel_name = programme.attrib.get("channel", "")
            if not any(name.lower() in channel_name.lower() for name in channel_names):
                continue

            start_str = programme.attrib.get("start")
            stop_str = programme.attrib.get("stop")

            try:
                start = datetime.strptime(start_str[:12], "%Y%m%d%H%M")
                stop = datetime.strptime(stop_str[:12], "%Y%m%d%H%M")
            except Exception:
                continue

            if not (now <= start <= end_date):
                continue

            title_el = programme.find("title")
            desc_el = programme.find("desc")

            title = title_el.text if title_el is not None else "Bez názvu"
            description = desc_el.text if desc_el is not None else ""

            # Přizpůsobeno formátu, který očekává sensor.py
            program = {
                "title": title,
                "supertitle": "",
                "episode_title": "",
                "description": description,
                "genre": "",
                "duration": f"{int((stop - start).total_seconds() / 60)} min",
                "date": start.strftime("%Y-%m-%d"),
                "time": start.strftime("%H:%M"),
                "episode": "",
                "link": "",
                "live": False,
                "premiere": False,
            }

            programs.append(program)

        programs.sort(key=lambda x: (x.get("date"), x.get("time")))
        _LOGGER.debug("Parsed %d programs for channel %s", len(programs), channel_id)
        return programs
