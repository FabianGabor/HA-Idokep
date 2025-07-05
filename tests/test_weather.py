"""Unit tests for the Időkép weather entity."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.components.weather.const import WeatherEntityFeature

from custom_components.idokep.const import DOMAIN
from custom_components.idokep.weather import IdokepWeatherEntity, async_setup_entry


class TestIdokepWeatherEntity:
    """Test cases for IdokepWeatherEntity."""

    def test_init_with_valid_location(self, mock_coordinator: Mock) -> None:
        """Test initialization with a valid location."""
        entity = IdokepWeatherEntity(mock_coordinator)

        # Test name property through public interface
        expected_name = "Budapest"
        expected_object_id = "idokep_budapest"
        expected_unique_id = "test_entry_id_weather_budapest"
        expected_features = (
            WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
        )

        # Access private attributes for testing (this is acceptable in unit tests)
        assert entity._attr_name == expected_name
        assert entity._attr_object_id == expected_object_id
        assert entity._attr_unique_id == expected_unique_id
        assert entity._attr_supported_features == expected_features

    def test_init_with_special_characters_in_location(
        self, mock_coordinator: Mock
    ) -> None:
        """Test initialization with special characters in location name."""
        mock_coordinator.config_entry.data = {"location": "New York City, NY!"}

        entity = IdokepWeatherEntity(mock_coordinator)

        expected_name = "New York City Ny"
        expected_object_id = "idokep_new_york_city_ny"
        expected_unique_id = "test_entry_id_weather_new_york_city_ny"

        assert entity._attr_name == expected_name
        assert entity._attr_object_id == expected_object_id
        assert entity._attr_unique_id == expected_unique_id

    def test_init_with_empty_location(self, mock_coordinator: Mock) -> None:
        """Test initialization with empty location."""
        mock_coordinator.config_entry.data = {"location": ""}

        entity = IdokepWeatherEntity(mock_coordinator)

        expected_name = "Unknown"
        expected_object_id = "idokep_unknown"
        expected_unique_id = "test_entry_id_weather_unknown"

        assert entity._attr_name == expected_name
        assert entity._attr_object_id == expected_object_id
        assert entity._attr_unique_id == expected_unique_id

    def test_init_with_location_only_special_chars(
        self, mock_coordinator: Mock
    ) -> None:
        """Test initialization with location containing only special characters."""
        mock_coordinator.config_entry.data = {"location": "!@#$%^&*()"}

        entity = IdokepWeatherEntity(mock_coordinator)

        expected_name = "Unknown"
        expected_object_id = "idokep_unknown"
        expected_unique_id = "test_entry_id_weather_unknown"

        assert entity._attr_name == expected_name
        assert entity._attr_object_id == expected_object_id
        assert entity._attr_unique_id == expected_unique_id

    def test_init_with_multiple_underscores(self, mock_coordinator: Mock) -> None:
        """Test initialization removes multiple consecutive underscores."""
        mock_coordinator.config_entry.data = {
            "location": "Test___Multiple___Underscores"
        }

        entity = IdokepWeatherEntity(mock_coordinator)

        expected_name = "Test Multiple Underscores"
        expected_object_id = "idokep_test_multiple_underscores"
        expected_unique_id = "test_entry_id_weather_test_multiple_underscores"

        assert entity._attr_name == expected_name
        assert entity._attr_object_id == expected_object_id
        assert entity._attr_unique_id == expected_unique_id

    def test_device_info_property(self, mock_coordinator: Mock) -> None:
        """Test device_info property returns correct device information."""
        entity = IdokepWeatherEntity(mock_coordinator)
        device_info = entity.device_info

        expected_device_info = {
            "identifiers": {(DOMAIN, "test_entry_id")},
            "name": "Időkép",
            "manufacturer": "Időkép",
            "model": "Időkép Weather Integration",
            "entry_type": "service",
        }

        assert device_info == expected_device_info

    def test_has_entity_name_property(self, mock_coordinator: Mock) -> None:
        """Test has_entity_name property returns True."""
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.has_entity_name is True

    def test_temperature_property(self, mock_coordinator: Mock) -> None:
        """Test temperature property returns coordinator data."""
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.temperature == 20.5

    def test_temperature_property_none(self, mock_coordinator: Mock) -> None:
        """Test temperature property when coordinator data is None."""
        mock_coordinator.data = {"temperature": None}
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.temperature is None

    def test_condition_property(self, mock_coordinator: Mock) -> None:
        """Test condition property returns coordinator data."""
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.condition == "sunny"

    def test_condition_property_none(self, mock_coordinator: Mock) -> None:
        """Test condition property when coordinator data is None."""
        mock_coordinator.data = {"condition": None}
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.condition is None

    def test_native_temperature_property(self, mock_coordinator: Mock) -> None:
        """Test native_temperature property returns float value."""
        entity = IdokepWeatherEntity(mock_coordinator)
        result = entity.native_temperature
        assert result == 20.5
        assert isinstance(result, float)

    def test_native_temperature_property_none(self, mock_coordinator: Mock) -> None:
        """Test native_temperature property when temperature is None."""
        mock_coordinator.data = {"temperature": None}
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.native_temperature is None

    def test_native_temperature_property_string_conversion(
        self, mock_coordinator: Mock
    ) -> None:
        """Test native_temperature property converts string to float."""
        mock_coordinator.data = {"temperature": "25.5"}
        entity = IdokepWeatherEntity(mock_coordinator)
        result = entity.native_temperature
        assert result == 25.5
        assert isinstance(result, float)

    def test_native_temperature_unit_property(self, mock_coordinator: Mock) -> None:
        """Test native_temperature_unit property returns Celsius."""
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.native_temperature_unit == "°C"

    def test_supported_forecast_types_property(self, mock_coordinator: Mock) -> None:
        """Test supported_forecast_types property returns correct types."""
        entity = IdokepWeatherEntity(mock_coordinator)
        assert entity.supported_forecast_types == ("hourly", "daily")

    def test_extra_state_attributes_property(self, mock_coordinator: Mock) -> None:
        """Test extra_state_attributes property returns correct attributes."""
        entity = IdokepWeatherEntity(mock_coordinator)
        attrs = entity.extra_state_attributes

        expected_attrs = {
            "temperature": 20.5,
            "precipitation": 0,
            "precipitation_probability": 10,
            "temperature_unit": "°C",
            "precipitation_unit": "mm",
            "short_forecast": "Sunny weather",
        }

        for key, value in expected_attrs.items():
            assert attrs[key] == value

    def test_extra_state_attributes_with_defaults(self, mock_coordinator: Mock) -> None:
        """Test extra_state_attributes property with default values."""
        mock_coordinator.data = {
            "temperature": 15.0,
            "short_forecast": "Cloudy",
        }
        entity = IdokepWeatherEntity(mock_coordinator)
        attrs = entity.extra_state_attributes

        assert attrs["temperature"] == 15.0
        assert attrs["precipitation"] == 0  # Default value
        assert attrs["precipitation_probability"] == 0  # Default value
        assert attrs["short_forecast"] == "Cloudy"

    @pytest.mark.asyncio
    async def test_async_forecast_hourly(self, mock_coordinator: Mock) -> None:
        """Test async_forecast_hourly returns hourly forecast data."""
        entity = IdokepWeatherEntity(mock_coordinator)
        forecast = await entity.async_forecast_hourly()

        expected_forecast = [
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
        ]

        assert forecast == expected_forecast

    @pytest.mark.asyncio
    async def test_async_forecast_hourly_empty(self, mock_coordinator: Mock) -> None:
        """Test async_forecast_hourly returns empty list when no data."""
        mock_coordinator.data = {}
        entity = IdokepWeatherEntity(mock_coordinator)
        forecast = await entity.async_forecast_hourly()

        assert forecast == []

    @pytest.mark.asyncio
    async def test_async_forecast_daily(self, mock_coordinator: Mock) -> None:
        """Test async_forecast_daily returns daily forecast data."""
        entity = IdokepWeatherEntity(mock_coordinator)
        forecast = await entity.async_forecast_daily()

        expected_forecast = [
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
        ]

        assert forecast == expected_forecast

    @pytest.mark.asyncio
    async def test_async_forecast_daily_empty(self, mock_coordinator: Mock) -> None:
        """Test async_forecast_daily returns empty list when no data."""
        mock_coordinator.data = {}
        entity = IdokepWeatherEntity(mock_coordinator)
        forecast = await entity.async_forecast_daily()

        assert forecast == []

    def test_device_info_attr_initialization(self, mock_coordinator: Mock) -> None:
        """Test _attr_device_info is properly set during initialization."""
        entity = IdokepWeatherEntity(mock_coordinator)

        # Test the identifiers and name from _attr_device_info
        device_info = entity._attr_device_info
        expected_identifiers = {(DOMAIN, "test_entry_id_budapest")}
        expected_name = "Időkép Budapest"

        assert device_info["identifiers"] == expected_identifiers
        assert device_info["name"] == expected_name

    def test_device_info_attr_with_special_location(
        self, mock_coordinator: Mock
    ) -> None:
        """Test _attr_device_info with special characters in location."""
        mock_coordinator.config_entry.data = {"location": "São Paulo, Brazil!"}
        entity = IdokepWeatherEntity(mock_coordinator)

        device_info = entity._attr_device_info

        # Original location should be preserved in device name
        assert device_info["name"] == "Időkép São Paulo, Brazil!"
        # But identifiers should use sanitized version
        expected_identifiers = {(DOMAIN, "test_entry_id_s_o_paulo_brazil")}
        assert device_info["identifiers"] == expected_identifiers


@pytest.mark.asyncio
async def test_async_setup_entry(mock_coordinator: Mock) -> None:
    """Test async_setup_entry function."""
    # Mock the required parameters
    mock_hass = Mock()
    mock_entry = Mock()
    mock_entry.runtime_data.coordinator = mock_coordinator
    # Ensure the coordinator has proper location data
    mock_coordinator.config_entry.data = {"location": "Budapest"}
    mock_async_add_entities = Mock()

    # Call the function
    await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)

    # Verify that async_add_entities was called with a weather entity
    mock_async_add_entities.assert_called_once()
    call_args = mock_async_add_entities.call_args[0][0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], IdokepWeatherEntity)
