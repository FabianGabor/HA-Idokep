"""Mock-based test configuration for super quick testing without Home Assistant."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_config_entry() -> Mock:
    """Return a mock config entry without Home Assistant imports."""
    mock_entry = Mock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {"location": "Budapest"}
    mock_entry.title = "Időkép Weather"
    return mock_entry


@pytest.fixture
def mock_hass() -> Mock:
    """Return a mock Home Assistant instance."""
    return Mock()


@pytest.fixture
def mock_weather_data() -> dict[str, Any]:
    """Return mock weather data."""
    return {
        "temperature": 22.5,
        "humidity": 65,
        "pressure": 1013.25,
        "wind_speed": 15.0,
        "wind_direction": "NW",
        "condition": "sunny",
        "visibility": 10.0,
        "forecast": [
            {
                "datetime": "2024-01-15T12:00:00Z",
                "temperature": 25.0,
                "condition": "sunny",
                "precipitation_probability": 10,
            }
        ],
    }


@pytest.fixture
def mock_idokep_data(mock_weather_data: dict[str, Any]) -> Mock:
    """Return mock IdokepData."""
    mock_data = Mock()
    mock_data.current = mock_weather_data
    mock_data.location = "Budapest"
    return mock_data


@pytest.fixture
def mock_coordinator(
    mock_config_entry: Mock, mock_hass: Mock, mock_idokep_data: Mock
) -> Mock:
    """Return a mock coordinator."""
    mock_coord = Mock()
    mock_coord.hass = mock_hass
    mock_coord.config_entry = mock_config_entry
    mock_coord.data = mock_idokep_data
    mock_coord.last_update_success = True
    mock_coord.async_add_listener = Mock()
    mock_coord.async_remove_listener = Mock()
    return mock_coord
