"""DataUpdateCoordinator for idokep."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IdokepApiClientAuthenticationError,
    IdokepApiClientError,
    IdokepApiClient,
)

if TYPE_CHECKING:
    from .data import IdokepConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class IdokepDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IdokepConfigEntry

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            location = self.config_entry.data["location"]
            data = await self.config_entry.runtime_data.client.async_get_weather_data(
                location
            )
            if not data:
                raise Exception("No weather data found for location: %s", location)
            return data
        except Exception as exception:
            raise UpdateFailed(exception) from exception
