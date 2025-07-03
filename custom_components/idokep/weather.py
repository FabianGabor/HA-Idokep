from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
)
from homeassistant.components.weather.const import WeatherEntityFeature

from .const import DOMAIN, NAME
from .coordinator import IdokepDataUpdateCoordinator
from .entity import IdokepEntity


class IdokepWeatherEntity(IdokepEntity, WeatherEntity):
    """Idokep Weather entity."""

    def __init__(self, coordinator: IdokepDataUpdateCoordinator) -> None:
        """Initialize the IdokepWeatherEntity with the given coordinator."""
        super().__init__(coordinator)
        self._attr_name = NAME
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
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
    def humidity(self) -> int | None:
        """Return the current humidity (%)."""
        return self.coordinator.data.get("humidity")

    @property
    def pressure(self) -> int | None:
        """Return the current pressure (hPa)."""
        return self.coordinator.data.get("pressure")

    @property
    def wind_speed(self) -> float | None:
        """Return the current wind speed (km/h)."""
        return self.coordinator.data.get("wind_speed")

    @property
    def wind_bearing(self) -> int | None:
        """Return the wind bearing (degrees)."""
        return self.coordinator.data.get("wind_bearing")

    @property
    def visibility(self) -> float | None:
        """Return the visibility (km)."""
        return self.coordinator.data.get("visibility")

    @property
    def supported_forecast_types(self) -> tuple[str, ...]:
        """Return the supported forecast types."""
        return ("hourly", "daily")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        attrs = dict(super().extra_state_attributes or {})
        attrs["temperature"] = self.temperature
        attrs["short_forecast"] = self.coordinator.data.get("short_forecast")
        return attrs

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

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        return self.coordinator.data.get("forecast", [])

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return the daily forecast in the format expected by Home Assistant UI."""
        return self.coordinator.data.get("daily_forecast", [])


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up the weather entity."""
    async_add_entities([IdokepWeatherEntity(entry.runtime_data.coordinator)])
