"""Sensor platform for Slovak TV Program."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, AVAILABLE_CHANNELS

_LOGGER = logging.getLogger(__name__)

# Maximální počet programů v atributech
MAX_UPCOMING_PROGRAMS = 10
MAX_ALL_PROGRAMS = 50  # Limit pro all_programs místo tisíců


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    channels = config_entry.data.get("channels", [])
    
    entities = []
    for channel_id in channels:
        entities.append(SkTVProgramSensor(coordinator, channel_id))
    
    async_add_entities(entities)


class SkTVProgramSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Slovak TV Program sensor."""

    def __init__(self, coordinator, channel_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._channel_id = channel_id
        self._channel_name = AVAILABLE_CHANNELS.get(channel_id, channel_id)
        self._attr_name = f"TV Program {self._channel_name}"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}"
        self._attr_icon = "mdi:television-classic"
        
        # Cache pro current/next programs
        self._cached_data: Optional[Tuple[Optional[Dict], List[Dict]]] = None
        self._last_update: Optional[datetime] = None

    def _get_programs(self) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get current and next programs with caching."""
        if not self.coordinator.data:
            return None, []
            
        channel_data = self.coordinator.data.get(self._channel_id, [])
        if not channel_data:
            return None, []
        
        now = dt_util.now()
        
        # Cache na 30 sekund - pokud se volá vícekrát za sebou
        if (self._cached_data and self._last_update and 
            (now - self._last_update).total_seconds() < 30):
            return self._cached_data
        
        current_program = None
        next_programs = []
        
        try:
            for program in channel_data:
                # Přeskočit programy bez časů
                start_dt = program.get('start_datetime')
                stop_dt = program.get('stop_datetime')
                
                if not start_dt or not stop_dt:
                    continue
                
                # Datetime by měly být už timezone-aware z API
                # Ale pro jistotu zkontrolujeme
                if start_dt.tzinfo is None:
                    start_dt = dt_util.as_local(start_dt)
                if stop_dt.tzinfo is None:
                    stop_dt = dt_util.as_local(stop_dt)
                
                # Aktuální program
                if start_dt <= now < stop_dt:
                    current_program = program
                # Budoucí programy (max 10)
                elif start_dt > now and len(next_programs) < MAX_UPCOMING_PROGRAMS:
                    next_programs.append(program)
                
                # Pokud máme current a dost next, můžeme přestat
                if current_program and len(next_programs) >= MAX_UPCOMING_PROGRAMS:
                    break
                    
        except Exception as err:
            _LOGGER.error("Error processing programs for %s: %s", self._channel_id, err)
            return None, []
        
        self._cached_data = (current_program, next_programs)
        self._last_update = now
        
        return current_program, next_programs

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        try:
            current_program, _ = self._get_programs()
            
            if current_program:
                return current_program.get('title', 'Neznámý pořad')
            
            return "Nedostupné"
            
        except Exception as err:
            _LOGGER.error("Error getting native_value for %s: %s", self._channel_id, err)
            return "Chyba"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        try:
            if not self.coordinator.data:
                return {}
                
            channel_data = self.coordinator.data.get(self._channel_id, [])
            if not channel_data:
                return {}
            
            # Použít cache místo opakovaného zpracování
            current_program, next_programs = self._get_programs()
            
            attributes = {
                "channel": self._channel_name,
                "channel_id": self._channel_id,
                "total_programs": len(channel_data),
            }
            
            # Current program details
            if current_program:
                attributes.update({
                    "current_title": current_program.get('title', ''),
                    "current_supertitle": current_program.get('supertitle', ''),
                    "current_episode_title": current_program.get('episode_title', ''),
                    "current_time": current_program.get('time', ''),
                    "current_date": current_program.get('date', ''),
                    "current_genre": current_program.get('genre', ''),
                    "current_duration": current_program.get('duration', ''),
                    "current_description": current_program.get('description', ''),
                    "current_episode": current_program.get('episode', ''),
                    "current_link": current_program.get('link', ''),
                    "current_live": current_program.get('live', False),
                    "current_premiere": current_program.get('premiere', False),
                })
            
            # Next programs - už máme z cache
            attributes["upcoming_programs"] = [
                {
                    "title": p.get('title', ''),
                    "time": p.get('time', ''),
                    "date": p.get('date', ''),
                    "genre": p.get('genre', ''),
                    "duration": p.get('duration', ''),
                    "description": p.get('description', ''),
                    "live": p.get('live', False),
                    "premiere": p.get('premiere', False),
                }
                for p in next_programs
            ]
            
            # KRITICKÁ ZMĚNA: Limit all_programs na prvních 50 místo všech!
            # Pro více programů by měl uživatel použít custom card s API voláním
            limited_programs = channel_data[:MAX_ALL_PROGRAMS]
            
            attributes["all_programs"] = [
                {
                    "title": p.get('title', ''),
                    "supertitle": p.get('supertitle', ''),
                    "episode_title": p.get('episode_title', ''),
                    "time": p.get('time', ''),
                    "date": p.get('date', ''),
                    "genre": p.get('genre', ''),
                    "duration": p.get('duration', ''),
                    "description": p.get('description', ''),
                    "episode": p.get('episode', ''),
                    "live": p.get('live', False),
                    "premiere": p.get('premiere', False),
                    "link": p.get('link', ''),
                }
                for p in limited_programs
            ]
            
            # Přidat info že je to omezeno
            if len(channel_data) > MAX_ALL_PROGRAMS:
                attributes["all_programs_note"] = f"Zobrazeno {MAX_ALL_PROGRAMS} z {len(channel_data)} programů"
            
            return attributes
            
        except Exception as err:
            _LOGGER.error("Error getting attributes for %s: %s", self._channel_id, err, exc_info=True)
            return {
                "channel": self._channel_name,
                "channel_id": self._channel_id,
                "error": str(err)
            }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
