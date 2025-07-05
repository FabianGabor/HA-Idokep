"""Tests for the Idokep sensor platform."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.core import HomeAssistant

from custom_components.idokep.sensor import (
    ENTITY_DESCRIPTIONS,
    IdokepSensor,
    async_setup_entry,
)


class TestIdokepSensorEntityDescriptions:
    """Test the sensor entity descriptions."""

    def test_entity_descriptions_count(self) -> None:
        """Test that we have the expected number of entity descriptions."""
        assert len(ENTITY_DESCRIPTIONS) == 6

    def test_entity_descriptions_keys(self) -> None:
        """Test that entity descriptions have the expected keys."""
        expected_keys = {
            "temperature",
            "condition",
            "condition_hu",
            "sunrise",
            "sunset",
            "short_forecast",
        }
        actual_keys = {desc.key for desc in ENTITY_DESCRIPTIONS}
        assert actual_keys == expected_keys

    def test_temperature_description(self) -> None:
        """Test the temperature entity description."""
        temp_desc = next(
            desc for desc in ENTITY_DESCRIPTIONS if desc.key == "temperature"
        )
        assert temp_desc.key == "temperature"
        assert temp_desc.translation_key == "temperature"
        assert temp_desc.icon == "mdi:thermometer"
        assert temp_desc.native_unit_of_measurement == "°C"
        assert temp_desc.device_class == SensorDeviceClass.TEMPERATURE
        assert temp_desc.state_class == "measurement"

    def test_condition_descriptions(self) -> None:
        """Test the condition entity descriptions."""
        condition_desc = next(
            desc for desc in ENTITY_DESCRIPTIONS if desc.key == "condition"
        )
        assert condition_desc.key == "condition"
        assert condition_desc.translation_key == "condition"
        assert condition_desc.icon == "mdi:weather-partly-cloudy"

        condition_hu_desc = next(
            desc for desc in ENTITY_DESCRIPTIONS if desc.key == "condition_hu"
        )
        assert condition_hu_desc.key == "condition_hu"
        assert condition_hu_desc.translation_key == "condition_hu"
        assert condition_hu_desc.icon == "mdi:weather-partly-cloudy"

    def test_sunrise_sunset_descriptions(self) -> None:
        """Test the sunrise and sunset entity descriptions."""
        sunrise_desc = next(
            desc for desc in ENTITY_DESCRIPTIONS if desc.key == "sunrise"
        )
        assert sunrise_desc.key == "sunrise"
        assert sunrise_desc.translation_key == "sunrise"
        assert sunrise_desc.icon == "mdi:weather-sunset-up"
        assert sunrise_desc.device_class == SensorDeviceClass.TIMESTAMP

        sunset_desc = next(desc for desc in ENTITY_DESCRIPTIONS if desc.key == "sunset")
        assert sunset_desc.key == "sunset"
        assert sunset_desc.translation_key == "sunset"
        assert sunset_desc.icon == "mdi:weather-sunset-down"
        assert sunset_desc.device_class == SensorDeviceClass.TIMESTAMP

    def test_short_forecast_description(self) -> None:
        """Test the short forecast entity description."""
        forecast_desc = next(
            desc for desc in ENTITY_DESCRIPTIONS if desc.key == "short_forecast"
        )
        assert forecast_desc.key == "short_forecast"
        assert forecast_desc.translation_key == "short_forecast"
        assert forecast_desc.icon == "mdi:weather-cloudy-clock"


class TestAsyncSetupEntry:
    """Test the async_setup_entry function."""

    async def test_async_setup_entry_creates_all_sensors(self) -> None:
        """Test that async_setup_entry creates all expected sensors."""
        hass = Mock(spec=HomeAssistant)
        entry = Mock()
        entry.runtime_data.coordinator = Mock()
        entry.runtime_data.coordinator.config_entry.entry_id = "test_entry"
        async_add_entities = Mock()

        await async_setup_entry(hass, entry, async_add_entities)

        # Check that async_add_entities was called with the correct number of sensors
        async_add_entities.assert_called_once()
        sensors = list(async_add_entities.call_args[0][0])
        assert len(sensors) == len(ENTITY_DESCRIPTIONS)

        # Check that all sensors are IdokepSensor instances
        for sensor in sensors:
            assert isinstance(sensor, IdokepSensor)


class TestIdokepSensor:
    """Test the IdokepSensor class."""

    def test_has_entity_name(self) -> None:
        """Test that has_entity_name returns True."""
        coordinator = Mock()
        entity_desc = SensorEntityDescription(key="test", translation_key="test")
        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.has_entity_name is True

    def test_initialization(self) -> None:
        """Test sensor initialization."""
        coordinator = Mock()
        coordinator.config_entry.entry_id = "test_entry"
        entity_desc = SensorEntityDescription(
            key="temperature", translation_key="temperature"
        )

        sensor = IdokepSensor(coordinator, entity_desc)

        assert sensor.coordinator == coordinator
        assert sensor.entity_description == entity_desc
        assert sensor._attr_unique_id == "test_entry_temperature"

    def test_native_value_string(self) -> None:
        """Test native_value with string data."""
        coordinator = Mock()
        coordinator.data = {"temperature": "20.5"}
        entity_desc = SensorEntityDescription(
            key="temperature", translation_key="temperature"
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.native_value == "20.5"

    def test_native_value_number(self) -> None:
        """Test native_value with numeric data."""
        coordinator = Mock()
        coordinator.data = {"temperature": 20.5}
        entity_desc = SensorEntityDescription(
            key="temperature", translation_key="temperature"
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.native_value == 20.5

    def test_native_value_none(self) -> None:
        """Test native_value when data is missing."""
        coordinator = Mock()
        coordinator.data = {}
        entity_desc = SensorEntityDescription(
            key="temperature", translation_key="temperature"
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.native_value is None

    def test_native_value_timestamp_valid(self) -> None:
        """Test native_value with valid timestamp data."""
        coordinator = Mock()
        coordinator.data = {"sunrise": "2023-10-01T06:00:00"}
        entity_desc = SensorEntityDescription(
            key="sunrise",
            translation_key="sunrise",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 10
        assert result.day == 1
        assert result.hour == 6
        assert result.minute == 0

    def test_native_value_timestamp_invalid(self) -> None:
        """Test native_value with invalid timestamp data."""
        coordinator = Mock()
        coordinator.data = {"sunrise": "invalid-date"}
        entity_desc = SensorEntityDescription(
            key="sunrise",
            translation_key="sunrise",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.native_value is None

    def test_native_value_timestamp_not_string(self) -> None:
        """Test native_value with non-string timestamp data."""
        coordinator = Mock()
        coordinator.data = {"sunrise": datetime(2023, 10, 1, 6, 0, 0, tzinfo=UTC)}
        entity_desc = SensorEntityDescription(
            key="sunrise",
            translation_key="sunrise",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        # Should return the datetime object as-is since it's not a string
        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.year == 2023

    def test_native_value_timestamp_none(self) -> None:
        """Test native_value when timestamp data is None."""
        coordinator = Mock()
        coordinator.data = {"sunrise": None}
        entity_desc = SensorEntityDescription(
            key="sunrise",
            translation_key="sunrise",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

        sensor = IdokepSensor(coordinator, entity_desc)
        assert sensor.native_value is None
