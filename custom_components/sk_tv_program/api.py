"""API client for Slovak TV Program from open-epg.com."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import XMLTV_API_URL, API_TIMEOUT, AVAILABLE_CHANNELS, DEFAULT_DAYS_AHEAD

_LOGGER = logging.getLogger(__name__)

# Maximální počet programů na kanál pro zabránění memory problémům
MAX_PROGRAMS_PER_CHANNEL = 500

class SkTVProgramAPI:
    """API client for Slovak TV Program."""

    def __init__(self, hass: HomeAssistant, channels: List[str]):
        """Initialize the API client."""
        self.hass = hass
        self.channels = channels or list(AVAILABLE_CHANNELS.keys())
        self.session = async_get_clientsession(hass)

    async def async_update_data(self) -> Dict[str, Any]:
        """Fetch data from open-epg.com XMLTV feed and return structured program info."""
        all_data: Dict[str, List[Dict[str, Any]]] = {}
        try:
            # Fetch open-epg.com feed
            xmltv_root = await self._fetch_xmltv(XMLTV_API_URL)
            
            if xmltv_root is None:
                _LOGGER.warning("No XMLTV data available from open-epg.com")
                return all_data

            # Parsování v executor aby neblokoval event loop
            for channel_id in self.channels:
                try:
                    # Použít executor pro CPU-intensive operace
                    programs = await self.hass.async_add_executor_job(
                        self._filter_channel_programs,
                        xmltv_root,
                        channel_id
                    )
                    
                    # Sort programs by date/time
                    programs.sort(key=lambda x: x.get("start_datetime", datetime.min))
                    
                    # Limit počtu programů
                    if len(programs) > MAX_PROGRAMS_PER_CHANNEL:
                        _LOGGER.warning(
                            "Channel %s has %d programs, limiting to %d",
                            channel_id, len(programs), MAX_PROGRAMS_PER_CHANNEL
                        )
                        programs = programs[:MAX_PROGRAMS_PER_CHANNEL]
                    
                    all_data[channel_id] = programs

                    if programs:
                        _LOGGER.debug("Found %d programs for channel %s", len(programs), channel_id)
                    else:
                        _LOGGER.warning("No programs found for channel %s", channel_id)
                        
                except Exception as err:
                    _LOGGER.error("Error processing channel %s: %s", channel_id, err, exc_info=True)
                    all_data[channel_id] = []

            _LOGGER.info("Fetched TV program for %d channels", len(all_data))
            return all_data

        except Exception as err:
            _LOGGER.error("Error fetching TV program: %s", err, exc_info=True)
            return all_data

    async def _fetch_xmltv(self, url: str) -> Optional[Element]:
        """Fetch XMLTV data from a given URL."""
        try:
            async with self.session.get(url, timeout=API_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check content size
                    content_size_mb = len(content) / (1024 * 1024)
                    if content_size_mb > 10:
                        _LOGGER.warning(
                            "Large XML file detected: %.2f MB. This may cause performance issues.",
                            content_size_mb
                        )
                    
                    # Parse XML v executor aby neblokoval
                    root = await self.hass.async_add_executor_job(
                        ET.fromstring,
                        content
                    )
                    
                    _LOGGER.debug("Successfully fetched XMLTV from %s (%.2f MB)", url, content_size_mb)
                    return root
                    
                _LOGGER.warning("Failed to fetch XMLTV: HTTP %s (%s)", response.status, url)
                return None
                
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching XMLTV data from %s", url)
            return None
        except Exception as err:
            _LOGGER.error("Error fetching XMLTV from %s: %s", url, err)
            return None

    def _parse_xmltv_datetime(self, dt_string: str) -> Optional[datetime]:
        """Parse XMLTV datetime format (YYYYMMDDHHmmss +ZONE) to timezone-aware datetime."""
        try:
            # XMLTV format: 20241105094000 +0100
            # Extract datetime part and timezone offset
            dt_part = dt_string[:14]  # YYYYMMDDHHmmss
            tz_part = dt_string[15:20] if len(dt_string) > 15 else ""  # +0100 or -0500
            
            # Parse the datetime
            naive_dt = datetime.strptime(dt_part, "%Y%m%d%H%M%S")
            
            # Parse timezone offset
            if tz_part:
                sign = 1 if tz_part[0] == '+' else -1
                hours = int(tz_part[1:3])
                minutes = int(tz_part[3:5])
                offset = timedelta(hours=sign * hours, minutes=sign * minutes)
                
                # Create timezone-aware datetime in UTC
                utc_dt = naive_dt - offset
                # Convert to local timezone
                aware_dt = dt_util.as_local(utc_dt.replace(tzinfo=dt_util.UTC))
            else:
                # No timezone info, assume local
                aware_dt = dt_util.as_local(naive_dt)
            
            return aware_dt
            
        except Exception as e:
            _LOGGER.debug("Error parsing XMLTV datetime %s: %s", dt_string, e)
            return None

    def _filter_channel_programs(self, xmltv_root: Element, channel_id: str) -> List[Dict[str, Any]]:
        """Filter and parse programs for a specific channel from XMLTV.
        
        Note: This method runs in executor to avoid blocking the event loop.
        """
        programs: List[Dict[str, Any]] = []
        if xmltv_root is None:
            return programs

        now = dt_util.now()
        end_date = now + timedelta(days=DEFAULT_DAYS_AHEAD)
        
        # Limit pro zabránění nekonečným smyčkám
        max_iterations = 10000
        iteration_count = 0

        # Channel ID mapping for open-epg.com XMLTV
        xmltv_channel_ids = {
            "rtvs1": ["Jednotka", "RTVS1", "RTVS 1", "rtvs1.sk", "jednotka.rtvs.sk"],
            "rtvs2": ["Dvojka", "RTVS2", "RTVS 2", "rtvs2.sk", "dvojka.rtvs.sk"],
            "rtvs24": ["RTVS24", "RTVS :24", ":24", "24.rtvs.sk"],
            "rtvs_sport": ["RTVSSport", "RTVS Sport", "sport.rtvs.sk"],
            "markiza": ["Markiza", "TV Markiza", "markiza.sk"],
            "doma": ["Doma", "TV Doma", "doma.sk"],
            "dajto": ["Dajto", "TV Dajto", "dajto.sk"],
            "joj": ["JOJ", "TV JOJ", "joj.sk"],
            "joj_plus": ["JOJPlus", "JOJ Plus", "Plus", "jojplus.sk"],
            "wau": ["WAU", "wau.sk"],
            "prima": ["Prima", "TV Prima", "prima.sk"],
            "ta3": ["TA3", "ta3.sk"],
        }

        channel_ids = [cid.lower() for cid in xmltv_channel_ids.get(channel_id, [channel_id])]

        try:
            for programme in xmltv_root.findall("programme"):
                iteration_count += 1
                
                # Safety check pro zabránění nekonečné smyčky
                if iteration_count > max_iterations:
                    _LOGGER.warning(
                        "Reached maximum iterations (%d) for channel %s",
                        max_iterations, channel_id
                    )
                    break
                
                # Také limit počtu programů
                if len(programs) >= MAX_PROGRAMS_PER_CHANNEL:
                    _LOGGER.debug(
                        "Reached program limit (%d) for channel %s",
                        MAX_PROGRAMS_PER_CHANNEL, channel_id
                    )
                    break
                
                channel_attr = programme.attrib.get("channel", "").lower()
                
                # Check if this program belongs to our channel
                if not any(cid in channel_attr for cid in channel_ids):
                    continue

                start_str = programme.attrib.get("start")
                stop_str = programme.attrib.get("stop")
                if not start_str or not stop_str:
                    continue

                # Parse XMLTV datetime with timezone
                start = self._parse_xmltv_datetime(start_str)
                stop = self._parse_xmltv_datetime(stop_str)
                
                if not start or not stop:
                    continue

                # Filter by date range (keep programs from 2 hours ago to 7 days ahead)
                if start < now - timedelta(hours=2) or start > end_date:
                    continue

                # Extract program details
                title_el = programme.find("title")
                desc_el = programme.find("desc")
                category_el = programme.find("category")
                sub_title_el = programme.find("sub-title")
                
                title = title_el.text if title_el is not None and title_el.text else "Bez názvu"
                description = desc_el.text if desc_el is not None and desc_el.text else ""
                genre = category_el.text if category_el is not None and category_el.text else ""
                episode_title = sub_title_el.text if sub_title_el is not None and sub_title_el.text else ""

                duration_minutes = int((stop - start).total_seconds() / 60)

                programs.append({
                    "title": title,
                    "supertitle": "",
                    "episode_title": episode_title,
                    "description": description,
                    "genre": genre,
                    "duration": f"{duration_minutes} min",
                    "date": start.strftime("%Y-%m-%d"),
                    "time": start.strftime("%H:%M"),
                    "stop_time": stop.strftime("%H:%M"),
                    "start_datetime": start,
                    "stop_datetime": stop,
                    "episode": "",
                    "link": "",
                    "live": False,
                    "premiere": False,
                })
                
        except Exception as err:
            _LOGGER.error("Error filtering programs for channel %s: %s", channel_id, err, exc_info=True)

        return programs
