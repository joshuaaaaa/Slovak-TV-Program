"""API client for Slovak TV Program with multiple XMLTV sources."""
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import XMLTV_API_URL, LEMONCZE_API_URL, API_TIMEOUT, AVAILABLE_CHANNELS, DEFAULT_DAYS_AHEAD

_LOGGER = logging.getLogger(__name__)

class SkTVProgramAPI:
    """API client for Slovak TV Program."""

    def __init__(self, hass: HomeAssistant, channels: List[str]):
        """Initialize the API client."""
        self.hass = hass
        self.channels = channels or list(AVAILABLE_CHANNELS.keys())
        self.session = async_get_clientsession(hass)

    async def async_update_data(self) -> Dict[str, Any]:
        """Fetch data from all XMLTV feeds and return structured program info."""
        all_data: Dict[str, List[Dict[str, Any]]] = {}
        try:
            # Fetch RTVS feed
            rtvs_root = await self._fetch_xmltv(XMLTV_API_URL)
            # Fetch LemonCZE feed (komerční kanály)
            lemon_root = await self._fetch_xmltv(LEMONCZE_API_URL)

            # Combine feeds
            xmltv_roots = [r for r in [rtvs_root, lemon_root] if r is not None]
            if not xmltv_roots:
                _LOGGER.warning("No XMLTV data available")
                return all_data

            for channel_id in self.channels:
                programs: List[Dict[str, Any]] = []
                for root in xmltv_roots:
                    programs += self._filter_channel_programs(root, channel_id)
                # Sort programs by date/time
                programs.sort(key=lambda x: (x.get("date"), x.get("time")))
                all_data[channel_id] = programs

                if not programs:
                    _LOGGER.warning("No programs found for channel %s", channel_id)

            _LOGGER.debug("Fetched TV program for %d channels", len(all_data))
            return all_data

        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err)
            return all_data

    async def _fetch_xmltv(self, url: str) -> Optional[Element]:
        """Fetch XMLTV data from a given URL."""
        try:
            async with self.session.get(url, timeout=API_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    return root
                _LOGGER.warning("Failed to fetch XMLTV: HTTP %s (%s)", response.status, url)
                return None
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching XMLTV data from %s", url)
            return None
        except Exception as err:
            _LOGGER.error("Error fetching XMLTV from %s: %s", url, err)
            return None

    def _filter_channel_programs(self, xmltv_root: Element, channel_id: str) -> List[Dict[str, Any]]:
        """Filter and parse programs for a specific channel from XMLTV."""
        programs: List[Dict[str, Any]] = []
        if xmltv_root is None:
            return programs

        now = datetime.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)

        # Names used in XMLTV for this channel
        channel_map = {
            "rtvs1": ["Jednotka", "RTVS 1", "RTVS1"],
            "rtvs2": ["Dvojka", "RTVS 2", "RTVS2"],
            "rtvs24": ["RTVS 24", ":24", "RTVS24"],
            "rtvs_sport": ["RTVS Sport", "RTVS Šport"],
            "markiza": ["Markíza", "Markiza"],
            "doma": ["Doma"],
            "dajto": ["Dajto"],
            "joj": ["JOJ"],
            "joj_plus": ["JOJ Plus", "Plus"],
            "wau": ["WAU"],
            "prima": ["Prima", "TV Prima"],
            "ta3": ["TA3"],
        }

        channel_names = [n.lower() for n in channel_map.get(channel_id, [channel_id])]

        for programme in xmltv_root.findall("programme"):
            channel_attr = programme.attrib.get("channel", "").lower()
            # Fallback: check display-name tag
            display_name_el = programme.find("channel/display-name")
            display_name = display_name_el.text.lower() if display_name_el is not None else ""

            if not any(name in channel_attr or name in display_name for name in channel_names):
                continue

            start_str = programme.attrib.get("start")
            stop_str = programme.attrib.get("stop")
            if not start_str or not stop_str:
                continue

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

            programs.append({
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
            })

        return programs
