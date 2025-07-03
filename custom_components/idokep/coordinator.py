"""DataUpdateCoordinator for idokep."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from .data import IdokepConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class NoWeatherDataError(Exception):
    """Exception raised when no weather data is found for a given location."""

    def __init__(self, location: str) -> None:
        """Initialize NoWeatherDataError with the given location."""
        super().__init__(f"No weather data found for location: {location}")

class IdokepDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IdokepConfigEntry

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        location = self.config_entry.data["location"]
        try:
            data = await self._fetch_weather_data(location)
        except NoWeatherDataError as exception:
            raise UpdateFailed(exception) from exception
        return data

    async def _fetch_weather_data(self, location: str) -> dict:
        data = await self.config_entry.runtime_data.client.async_get_weather_data(
            location
        )
        if not data:
            raise NoWeatherDataError(location)
        return data
