"""Sensor platform for Slovak TV Program."""
import logging
import json
import os
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
    coordinators = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for channel_id, channel_data in coordinators.items():
        coordinator = channel_data["coordinator"]
        entities.append(SkTVProgramSensor(hass, coordinator, channel_id))

    async_add_entities(entities)


class SkTVProgramSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Slovak TV Program sensor."""

    def __init__(self, hass: HomeAssistant, coordinator, channel_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hass = hass
        self._channel_id = channel_id
        self._channel_name = AVAILABLE_CHANNELS.get(channel_id, channel_id)
        self._attr_name = f"TV Program {self._channel_name}"
        self._attr_unique_id = f"{DOMAIN}_{channel_id}"
        self._attr_icon = "mdi:television-classic"

        # Cache pro current/next programs
        self._cached_data: Optional[Tuple[Optional[Dict], List[Dict]]] = None
        self._last_update: Optional[datetime] = None

        # JSON storage path and cached JSON data
        storage_dir = os.path.join(hass.config.path(), ".storage", DOMAIN)
        os.makedirs(storage_dir, exist_ok=True)
        self._json_file = os.path.join(storage_dir, f"{channel_id}.json")
        self._json_cached_data: List[Dict[str, Any]] = []

        # Load cached data from JSON on init
        self._load_from_json()

    def _load_from_json(self) -> None:
        """Load cached data from JSON file."""
        if os.path.exists(self._json_file):
            try:
                with open(self._json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for program in data:
                        if 'start_datetime' in program and isinstance(program['start_datetime'], str):
                            program['start_datetime'] = datetime.fromisoformat(program['start_datetime'])
                        if 'stop_datetime' in program and isinstance(program['stop_datetime'], str):
                            program['stop_datetime'] = datetime.fromisoformat(program['stop_datetime'])
                    self._json_cached_data = data
                    _LOGGER.info("Loaded %d programs from JSON for %s", len(data), self._channel_id)
            except Exception as err:
                _LOGGER.error("Error loading JSON for %s: %s", self._channel_id, err)
                self._json_cached_data = []

    def _save_to_json(self, data: List[Dict[str, Any]]) -> None:
        """Save data to JSON file."""
        try:
            # Convert datetime objects to strings for JSON serialization
            json_data = []
            for program in data:
                program_copy = program.copy()
                if 'start_datetime' in program_copy and isinstance(program_copy['start_datetime'], datetime):
                    program_copy['start_datetime'] = program_copy['start_datetime'].isoformat()
                if 'stop_datetime' in program_copy and isinstance(program_copy['stop_datetime'], datetime):
                    program_copy['stop_datetime'] = program_copy['stop_datetime'].isoformat()
                json_data.append(program_copy)

            with open(self._json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            _LOGGER.debug("Saved %d programs to JSON for %s", len(json_data), self._channel_id)
        except Exception as err:
            _LOGGER.error("Error saving JSON for %s: %s", self._channel_id, err)

    @property
    def _channel_data(self) -> List[Dict[str, Any]]:
        """Get channel data from coordinator or JSON cache."""
        if self.coordinator.data and isinstance(self.coordinator.data, list):
            # Data from coordinator
            return self.coordinator.data
        # Fallback to JSON cached data if coordinator has no data
        return self._json_cached_data

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        # Save to JSON when coordinator updates
        if self.coordinator.data and isinstance(self.coordinator.data, list):
            self._json_cached_data = self.coordinator.data
            self._save_to_json(self.coordinator.data)
            _LOGGER.info("Updated data for %s: %d programs", self._channel_id, len(self.coordinator.data))

    def _get_programs(self) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get current and next programs with caching."""
        channel_data = self._channel_data
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
            channel_data = self._channel_data
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
