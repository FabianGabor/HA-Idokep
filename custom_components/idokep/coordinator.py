"""DataUpdateCoordinator for idokep."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IdokepApiClientConnectivityError

if TYPE_CHECKING:
    from datetime import timedelta
    from logging import Logger

    from homeassistant.core import HomeAssistant

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

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        update_interval: timedelta,
        config_entry: IdokepConfigEntry,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass, logger=logger, name=name, update_interval=update_interval
        )
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        location = self.config_entry.data["location"]
        try:
            data = await self._fetch_weather_data(location)
        except IdokepApiClientConnectivityError:
            # Don't raise UpdateFailed for connectivity issues, just log and
            # return empty dict
            # This prevents Home Assistant from marking entities as unavailable
            self.logger.info(
                "No internet connectivity to idokep.hu, keeping existing data"
            )
            return self.data or {}
        except NoWeatherDataError as exception:
            raise UpdateFailed(exception) from exception
        return data

    async def _fetch_weather_data(self, location: str) -> dict:
        """Fetch weather data for a given location."""
        data = await self.config_entry.runtime_data.client.async_get_weather_data(
            location
        )
        if not data:
            raise NoWeatherDataError(location)
        return data
