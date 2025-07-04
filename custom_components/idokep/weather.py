"""Időkép Weather Entity for Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
)
from homeassistant.components.weather.const import WeatherEntityFeature

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
        self._attr_name = NAME
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_weather"
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
        )
        _LOGGER.debug(
            "Initialized weather entity with unique_id: %s", self._attr_unique_id
        )

    @property
    def temperature(self) -> int | None:
        """Return the current temperature."""
        return self.coordinator.data.get("temperature")

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        return self.coordinator.data.get("condition")

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
        attrs["temperature_unit"] = "°C"
        attrs["precipitation_unit"] = "mm"
        attrs["short_forecast"] = self.coordinator.data.get("short_forecast")
        return attrs

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        return self.coordinator.data.get("forecast", [])

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return the daily forecast in the format expected by Home Assistant UI."""
        return self.coordinator.data.get("daily_forecast", [])


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the weather entity."""
    _LOGGER.debug("Setting up Időkép weather entity")
    weather_entity = IdokepWeatherEntity(entry.runtime_data.coordinator)
    _LOGGER.debug("Created weather entity with unique_id: %s", weather_entity.unique_id)
    async_add_entities([weather_entity])
    _LOGGER.debug("Added weather entity to Home Assistant")
