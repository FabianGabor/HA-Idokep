"""Additional unit tests for Időkép coordinator and entity."""

from __future__ import annotations

from datetime import timedelta
from logging import getLogger
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.idokep.coordinator import (
    IdokepDataUpdateCoordinator,
    NoWeatherDataError,
)


class TestIdokepDataUpdateCoordinator:
    """Test cases for IdokepDataUpdateCoordinator."""

    def test_no_weather_data_error_initialization(self) -> None:
        """Test NoWeatherDataError initialization."""
        location = "TestLocation"
        error = NoWeatherDataError(location)

        expected_message = f"No weather data found for location: {location}"
        assert str(error) == expected_message

    def test_coordinator_initialization(self, mock_hass: Mock) -> None:
        """Test coordinator initialization."""
        logger = getLogger(__name__)
        name = "test_coordinator"
        update_interval = timedelta(minutes=30)
        mock_config_entry = Mock()

        coordinator = IdokepDataUpdateCoordinator(
            mock_hass, logger, name, update_interval, mock_config_entry
        )

        assert coordinator.hass == mock_hass
        assert coordinator.config_entry == mock_config_entry
        assert coordinator.name == name
        assert coordinator.update_interval == update_interval

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, mock_hass: Mock) -> None:
        """Test successful data update."""
        logger = getLogger(__name__)
        name = "test_coordinator"
        update_interval = timedelta(minutes=30)
        mock_config_entry = Mock()
        mock_config_entry.data = {"location": "Budapest"}

        coordinator = IdokepDataUpdateCoordinator(
            mock_hass, logger, name, update_interval, mock_config_entry
        )

        # Mock the _fetch_weather_data method
        expected_data = {"temperature": 25.0, "condition": "sunny"}
        coordinator._fetch_weather_data = AsyncMock(return_value=expected_data)

        result = await coordinator._async_update_data()

        assert result == expected_data
        coordinator._fetch_weather_data.assert_called_once_with("Budapest")

    @pytest.mark.asyncio
    async def test_async_update_data_no_weather_error(self, mock_hass: Mock) -> None:
        """Test data update with NoWeatherDataError."""
        logger = getLogger(__name__)
        name = "test_coordinator"
        update_interval = timedelta(minutes=30)
        mock_config_entry = Mock()
        mock_config_entry.data = {"location": "InvalidLocation"}

        coordinator = IdokepDataUpdateCoordinator(
            mock_hass, logger, name, update_interval, mock_config_entry
        )

        # Mock the _fetch_weather_data method to raise NoWeatherDataError
        coordinator._fetch_weather_data = AsyncMock(
            side_effect=NoWeatherDataError("InvalidLocation")
        )

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        # Verify the original NoWeatherDataError is wrapped in UpdateFailed
        assert "No weather data found for location: InvalidLocation" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_async_update_data_general_exception(self, mock_hass: Mock) -> None:
        """Test data update with general exception."""
        logger = getLogger(__name__)
        name = "test_coordinator"
        update_interval = timedelta(minutes=30)
        mock_config_entry = Mock()
        mock_config_entry.data = {"location": "Budapest"}

        coordinator = IdokepDataUpdateCoordinator(
            mock_hass, logger, name, update_interval, mock_config_entry
        )

        # Mock the _fetch_weather_data method to raise a general exception
        coordinator._fetch_weather_data = AsyncMock(
            side_effect=Exception("Network error")
        )

        # The coordinator wraps any exception in UpdateFailed, not just
        # NoWeatherDataError
        # So we expect the original Exception to propagate
        with pytest.raises(Exception, match="Network error") as exc_info:
            await coordinator._async_update_data()

        assert "Network error" in str(exc_info.value)
