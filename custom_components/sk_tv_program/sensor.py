"""Sensor platform for Slovak TV Program."""
import logging
from datetime import datetime
from typing import Any, Dict, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, AVAILABLE_CHANNELS

_LOGGER = logging.getLogger(__name__)


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

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available")
            return "Nedostupné"
            
        channel_data = self.coordinator.data.get(self._channel_id, [])
        if not channel_data:
            _LOGGER.debug("No channel data for %s", self._channel_id)
            return "Nedostupné"
            
        # Find current program
        now = datetime.now()
        current_program = None
        
        for program in channel_data:
            start_dt = program.get('start_datetime')
            stop_dt = program.get('stop_datetime')
            
            if start_dt and stop_dt:
                # Check if program is currently running
                if start_dt <= now < stop_dt:
                    current_program = program
                    break
                    
        if current_program:
            return current_program.get('title', 'Neznámý pořad')
        
        return "Nedostupné"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
        channel_data = self.coordinator.data.get(self._channel_id, [])
        if not channel_data:
            return {}
            
        now = datetime.now()
        
        # Find current and next programs
        current_program = None
        next_programs = []
        
        for program in channel_data:
            start_dt = program.get('start_datetime')
            stop_dt = program.get('stop_datetime')
            
            if not start_dt or not stop_dt:
                continue
                
            # Current program
            if start_dt <= now < stop_dt:
                current_program = program
            # Future programs
            elif start_dt > now and len(next_programs) < 10:
                next_programs.append(program)
        
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
        
        # Next programs
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
        
        # All programs for custom card
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
            for p in channel_data
        ]
        
        return attributes
