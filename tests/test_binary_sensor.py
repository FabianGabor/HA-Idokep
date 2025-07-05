"""Unit tests for the Időkép binary sensor platform."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant

from custom_components.idokep.binary_sensor import (
    ENTITY_DESCRIPTIONS,
    IdokepBinarySensor,
    async_setup_entry,
)


class TestIdokepBinarySensor:
    """Test cases for IdokepBinarySensor."""

    def test_entity_descriptions(self) -> None:
        """Test that ENTITY_DESCRIPTIONS is properly defined."""
        assert len(ENTITY_DESCRIPTIONS) == 1
        description = ENTITY_DESCRIPTIONS[0]
        assert description.key == "idokep"
        assert description.name == "Idokep Binary Sensor"
        assert description.device_class == BinarySensorDeviceClass.CONNECTIVITY

    @pytest.mark.asyncio
    async def test_async_setup_entry(self) -> None:
        """Test the setup of binary sensor entities."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock()
        mock_coordinator = Mock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_async_add_entities = Mock()

        # Call the setup function
        await async_setup_entry(mock_hass, mock_entry, mock_async_add_entities)

        # Verify that async_add_entities was called
        mock_async_add_entities.assert_called_once()

        # Get the entities that were added
        added_entities = list(mock_async_add_entities.call_args[0][0])
        assert len(added_entities) == 1

        # Verify the entity is of correct type
        entity = added_entities[0]
        assert isinstance(entity, IdokepBinarySensor)

    def test_binary_sensor_initialization(self, mock_coordinator: Mock) -> None:
        """Test initialization of binary sensor."""
        entity_description = ENTITY_DESCRIPTIONS[0]

        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Verify initialization
        assert binary_sensor.coordinator is mock_coordinator
        assert binary_sensor.entity_description is entity_description
        assert binary_sensor.entity_description.key == "idokep"

    def test_is_on_true(self, mock_coordinator: Mock) -> None:
        """Test is_on property returns True when condition is met."""
        # Setup coordinator data to return "foo" for title
        mock_coordinator.data = {"title": "foo"}

        entity_description = ENTITY_DESCRIPTIONS[0]
        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Test that is_on returns True
        assert binary_sensor.is_on is True

    def test_is_on_false(self, mock_coordinator: Mock) -> None:
        """Test is_on property returns False when condition is not met."""
        # Setup coordinator data to return something other than "foo"
        mock_coordinator.data = {"title": "bar"}

        entity_description = ENTITY_DESCRIPTIONS[0]
        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Test that is_on returns False
        assert binary_sensor.is_on is False

    def test_is_on_no_title(self, mock_coordinator: Mock) -> None:
        """Test is_on property returns False when title is missing."""
        # Setup coordinator data without title
        mock_coordinator.data = {}

        entity_description = ENTITY_DESCRIPTIONS[0]
        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Test that is_on returns False
        assert binary_sensor.is_on is False

    def test_is_on_empty_title(self, mock_coordinator: Mock) -> None:
        """Test is_on property returns False when title is empty."""
        # Setup coordinator data with empty title
        mock_coordinator.data = {"title": ""}

        entity_description = ENTITY_DESCRIPTIONS[0]
        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Test that is_on returns False
        assert binary_sensor.is_on is False

    def test_binary_sensor_inheritance(self, mock_coordinator: Mock) -> None:
        """Test that binary sensor inherits from correct base classes."""
        entity_description = ENTITY_DESCRIPTIONS[0]
        binary_sensor = IdokepBinarySensor(
            coordinator=mock_coordinator,
            entity_description=entity_description,
        )

        # Verify inheritance - basic checks
        assert isinstance(binary_sensor, IdokepBinarySensor)
        assert hasattr(binary_sensor, "coordinator")
        assert hasattr(binary_sensor, "entity_description")
