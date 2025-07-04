"""Conftest file for Időkép integration tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.idokep.const import DOMAIN
from custom_components.idokep.coordinator import IdokepDataUpdateCoordinator
from custom_components.idokep.data import IdokepData


@pytest.fixture
def mock_config_entry() -> Mock:
    """Return a mock config entry."""
    return Mock(spec=ConfigEntry)


@pytest.fixture
def mock_config_entry_data() -> dict[str, str]:
    """Return mock config entry data."""
    return {
        "location": "Budapest",
    }


@pytest.fixture
def mock_hass() -> Mock:
    """Return a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    return hass


@pytest.fixture
def mock_coordinator_data() -> dict[str, Any]:
    """Return mock coordinator data."""
    return {
        "temperature": 20.5,
        "condition": "sunny",
        "precipitation": 0,
        "precipitation_probability": 10,
        "short_forecast": "Sunny weather",
        "hourly_forecast": [
            {
                "datetime": "2025-07-04T12:00:00",
                "temperature": 22.0,
                "condition": "sunny",
                "precipitation": 0,
            },
            {
                "datetime": "2025-07-04T13:00:00",
                "temperature": 23.5,
                "condition": "partly-cloudy",
                "precipitation": 0,
            },
        ],
        "daily_forecast": [
            {
                "datetime": "2025-07-04",
                "temperature": 25.0,
                "templow": 15.0,
                "condition": "sunny",
                "precipitation": 0,
            },
            {
                "datetime": "2025-07-05",
                "temperature": 27.0,
                "templow": 17.0,
                "condition": "partly-cloudy",
                "precipitation": 2.5,
            },
        ],
    }


@pytest.fixture
def mock_coordinator(
    mock_hass: Mock, mock_config_entry: Mock, mock_coordinator_data: dict[str, Any]
) -> Mock:
    """Return a mock coordinator."""
    coordinator = Mock(spec=IdokepDataUpdateCoordinator)
    coordinator.hass = mock_hass
    coordinator.config_entry = mock_config_entry
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.domain = DOMAIN
    coordinator.config_entry.data = {"location": "Budapest"}
    coordinator.data = mock_coordinator_data
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_idokep_data() -> Mock:
    """Return mock IdokepData."""
    return Mock(spec=IdokepData)


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Return a mock API client."""
    client = AsyncMock()
    client.get_weather_data = AsyncMock()
    return client
