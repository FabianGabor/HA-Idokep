"""Időkép Weather Entity for Home Assistant."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    Forecast,
    WeatherEntity,
)
from homeassistant.components.weather.const import WeatherEntityFeature
from homeassistant.helpers import sun
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, NAME
from .entity import IdokepEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import IdokepDataUpdateCoordinator
    from .data import IdokepConfigEntry

_LOGGER = logging.getLogger(__name__)


class IdokepWeatherEntity(IdokepEntity, WeatherEntity):
    """Idokep Weather entity."""

    @property
    def device_info(self) -> dict:
        """Return device information for the integration."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": NAME,
            "manufacturer": NAME,
            "model": "Időkép Weather Integration",
            "entry_type": "service",
        }

    @property
    def has_entity_name(self) -> bool:
        """Return True if the entity has a name."""
        return True

    def __init__(self, coordinator: IdokepDataUpdateCoordinator) -> None:
        """Initialize the IdokepWeatherEntity with the given coordinator."""
        super().__init__(coordinator)
        location = coordinator.config_entry.data.get("location", "")
        # Sanitize location for entity ID (remove special chars, etc.)
        sanitized_location = re.sub(
            r"[^a-zA-Z0-9_-]", "_", location.lower().replace(" ", "_").replace("-", "_")
        )
        # Remove multiple consecutive underscores
        sanitized_location = re.sub(r"_+", "_", sanitized_location).strip("_")
        # Fallback to 'unknown' if location becomes empty after sanitization
        if not sanitized_location:
            sanitized_location = "unknown"

        # Set entity name to sanitized location for proper entity_id
        self._attr_name = sanitized_location.replace("_", " ").title()
        # Set the object_id to control the entity_id generation
        self._attr_object_id = f"idokep_{sanitized_location}"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_weather_{sanitized_location}"
        )
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
        )
        _LOGGER.debug(
            "Initialized weather entity with unique_id: %s for location: %s",
            self._attr_unique_id,
            location,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    f"{coordinator.config_entry.entry_id}_{sanitized_location}",
                ),
            },
            name=f"Időkép {location}",
        )

    @property
    def temperature(self) -> int | None:
        """Return the current temperature."""
        return self.coordinator.data.get("temperature")

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        condition = self.coordinator.data.get("condition")
        if condition == ATTR_CONDITION_SUNNY and not sun.is_up(self.hass):
            return ATTR_CONDITION_CLEAR_NIGHT
        return condition

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature in native units."""
        temp = self.coordinator.data.get("temperature")
        return float(temp) if temp is not None else None

    @property
    def native_temperature_unit(self) -> str:
        """Return the unit of measurement for temperature."""
        return "°C"

    @property
    def supported_forecast_types(self) -> tuple[str, ...]:
        """Return the supported forecast types."""
        return ("hourly", "daily")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        attrs = dict(super().extra_state_attributes or {})
        attrs["temperature"] = self.temperature
        attrs["precipitation"] = self.coordinator.data.get("precipitation", 0)
        attrs["precipitation_probability"] = self.coordinator.data.get(
            "precipitation_probability", 0
        )
        attrs["temperature_unit"] = "°C"
        attrs["precipitation_unit"] = "mm"
        attrs["short_forecast"] = self.coordinator.data.get("short_forecast")

        return attrs

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        return self.coordinator.data.get("hourly_forecast", [])

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return the daily forecast."""
        return self.coordinator.data.get("daily_forecast", [])

    async def async_forecast_twice_daily(self) -> list[Forecast]:
        """Return the twice daily forecast."""
        # Return daily forecast as we don't have specific twice-daily data
        return self.coordinator.data.get("daily_forecast", [])


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the weather entity."""
    weather_entity = IdokepWeatherEntity(entry.runtime_data.coordinator)
    async_add_entities([weather_entity])
