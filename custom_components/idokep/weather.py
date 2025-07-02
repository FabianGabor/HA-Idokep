from homeassistant.components.weather import WeatherEntity
from .entity import IdokepEntity


class IdokepWeatherEntity(IdokepEntity, WeatherEntity):
    """Idokep Weather entity."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Idokep Weather"

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
    def forecast(self):
        """Return the forecast (not implemented)."""
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the weather entity."""
    async_add_entities([IdokepWeatherEntity(entry.runtime_data.coordinator)])
