"""API client for Slovak TV Program."""
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from defusedxml import ElementTree as ET

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
            
            # Fetch XMLTV data
            xmltv_data = await self._fetch_xmltv()
            
            # Parse and organize by channel
            for channel_id in self.channels:
                channel_programs = self._filter_channel_programs(xmltv_data, channel_id)
                all_data[channel_id] = channel_programs
                
            return all_data
            
        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err)
            raise
    
    async def _fetch_xmltv(self) -> ET.Element:
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
    
    def _filter_channel_programs(self, xmltv_root: ET.Element, channel_id: str) -> List[Dict[str, Any]]:
        """Filter and parse programs for specific channel."""
        programs = []
        
        if xmltv_root is None:
            return programs
            
        now = datetime.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)
        
        # Map internal channel IDs to XMLTV channel IDs
        channel_map = {
            "rtvs1": ["Jednotka", "RTVS 1", "RTVS1"],
            "rtvs2": ["Dvojka", "RTVS 2", "RTVS2"],
            "rtvs24": ["RTVS 24", ":24", "RTVS24"],
            "rtvs_sport": ["RTVS Sport", "RTVS Šport"],
            "markiza": ["Markiza", "TV Markiza"],
            "doma": ["Doma", "TV Doma"],
            "dajto": ["Dajto", "TV Dajto"],
            "joj": ["JOJ", "TV JOJ"],
            "joj_plus": ["JOJ Plus", "JOJ+"],
            "wau": ["WAU"],
            "prima": ["Prima", "TV Prima"],
            "ta3": ["TA3"],
        }
        
        channel_names = channel_map.get(channel_id, [channel_id])
        
        try:
            # Find all programme elements
            for programme in xmltv_root.findall('.//programme'):
                # Get channel attribute
                channel_attr = programme.get('channel', '')
                
                # Check if this program belongs to our channel
                if not any(name in channel_attr for name in channel_names):
                    continue
                
                # Parse start and stop times
                start_str = programme.get('start', '')
                stop_str = programme.get('stop', '')
                
                if not start_str:
                    continue
                    
                # Parse XMLTV datetime format (YYYYMMDDHHmmss +ZONE)
                try:
                    start_dt = datetime.strptime(start_str[:14], "%Y%m%d%H%M%S")
                    
                    # Filter by date range
                    if start_dt < now or start_dt > end_date:
                        continue
                        
                    stop_dt = None
                    if stop_str:
                        stop_dt = datetime.strptime(stop_str[:14], "%Y%m%d%H%M%S")
                        
                except ValueError:
                    continue
                
                # Extract program info
                program = {
                    'date': start_dt.strftime("%Y-%m-%d"),
                    'time': start_dt.strftime("%H:%M"),
                    'datetime': start_dt,
                }
                
                # Title
                title_elem = programme.find('title')
                if title_elem is not None:
                    program['title'] = title_elem.text or "Neznámy pořad"
                else:
                    program['title'] = "Neznámy pořad"
                
                # Subtitle
                sub_title_elem = programme.find('sub-title')
                program['episode_title'] = sub_title_elem.text if sub_title_elem is not None and sub_title_elem.text else ""
                
                # Description
                desc_elem = programme.find('desc')
                program['description'] = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                
                # Category (Genre)
                category_elem = programme.find('category')
                program['genre'] = category_elem.text if category_elem is not None and category_elem.text else ""
                
                # Duration
                if stop_dt:
                    duration_minutes = int((stop_dt - start_dt).total_seconds() / 60)
                    program['duration'] = f"{duration_minutes:03d}:00"
                else:
                    program['duration'] = ""
                
                # Episode info
                episode_elem = programme.find('episode-num')
                program['episode'] = episode_elem.text if episode_elem is not None and episode_elem.text else ""
                
                # Additional attributes
                program['supertitle'] = ""
                program['live'] = False
                program['premiere'] = False
                program['link'] = ""
                
                programs.append(program)
                
        except Exception as err:
            _LOGGER.error("Error parsing XMLTV for channel %s: %s", channel_id, err)
            
        # Sort by datetime
        programs.sort(key=lambda x: x.get('datetime', datetime.min))
        
        # Remove datetime key (used only for sorting)
        for p in programs:
            if 'datetime' in p:
                del p['datetime']
                
        return programs
