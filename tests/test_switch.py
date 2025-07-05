"""Tests for the Idokep switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.core import HomeAssistant

from custom_components.idokep.switch import (
    ENTITY_DESCRIPTIONS,
    IdokepSwitch,
    async_setup_entry,
)


class TestIdokepSwitchEntityDescriptions:
    """Test the switch entity descriptions."""

    def test_entity_descriptions_count(self) -> None:
        """Test that we have the expected number of entity descriptions."""
        assert len(ENTITY_DESCRIPTIONS) == 1

    def test_entity_descriptions_keys(self) -> None:
        """Test that entity descriptions have the expected keys."""
        expected_keys = {"idokep"}
        actual_keys = {desc.key for desc in ENTITY_DESCRIPTIONS}
        assert actual_keys == expected_keys

    def test_idokep_description(self) -> None:
        """Test the idokep entity description."""
        desc = ENTITY_DESCRIPTIONS[0]
        assert desc.key == "idokep"
        assert desc.name == "Integration Switch"
        assert desc.icon == "mdi:format-quote-close"


class TestAsyncSetupEntry:
    """Test the async_setup_entry function."""

    async def test_async_setup_entry_creates_switch(self) -> None:
        """Test that async_setup_entry creates expected switch."""
        hass = Mock(spec=HomeAssistant)
        entry = Mock()
        entry.runtime_data.coordinator = Mock()
        async_add_entities = Mock()

        await async_setup_entry(hass, entry, async_add_entities)

        # Check that async_add_entities was called with the correct number of switches
        async_add_entities.assert_called_once()
        switches = list(async_add_entities.call_args[0][0])
        assert len(switches) == len(ENTITY_DESCRIPTIONS)

        # Check that all switches are IdokepSwitch instances
        for switch in switches:
            assert isinstance(switch, IdokepSwitch)


class TestIdokepSwitch:
    """Test the IdokepSwitch class."""

    def test_initialization(self) -> None:
        """Test switch initialization."""
        coordinator = Mock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")

        switch = IdokepSwitch(coordinator, entity_desc)

        assert switch.coordinator == coordinator
        assert switch.entity_description == entity_desc

    def test_is_on_true(self) -> None:
        """Test is_on property when condition is met."""
        coordinator = Mock()
        coordinator.data = {"title": "foo"}
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")

        switch = IdokepSwitch(coordinator, entity_desc)
        assert switch.is_on is True

    def test_is_on_false(self) -> None:
        """Test is_on property when condition is not met."""
        coordinator = Mock()
        coordinator.data = {"title": "bar"}
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")

        switch = IdokepSwitch(coordinator, entity_desc)
        assert switch.is_on is False

    def test_is_on_no_title(self) -> None:
        """Test is_on property when title is missing."""
        coordinator = Mock()
        coordinator.data = {}
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")

        switch = IdokepSwitch(coordinator, entity_desc)
        assert switch.is_on is False

    def test_turn_on_raises_not_implemented(self) -> None:
        """Test that turn_on raises NotImplementedError."""
        coordinator = Mock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        with pytest.raises(NotImplementedError):
            switch.turn_on()

    def test_turn_off_raises_not_implemented(self) -> None:
        """Test that turn_off raises NotImplementedError."""
        coordinator = Mock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        with pytest.raises(NotImplementedError):
            switch.turn_off()

    async def test_async_turn_on(self) -> None:
        """Test async turn on functionality."""
        coordinator = AsyncMock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        await switch.async_turn_on()

        coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off(self) -> None:
        """Test async turn off functionality."""
        coordinator = AsyncMock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        await switch.async_turn_off()

        coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_on_with_kwargs(self) -> None:
        """Test async turn on with extra keyword arguments."""
        coordinator = AsyncMock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        await switch.async_turn_on(extra_param="value", another_param=123)

        coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off_with_kwargs(self) -> None:
        """Test async turn off with extra keyword arguments."""
        coordinator = AsyncMock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        await switch.async_turn_off(extra_param="value", another_param=123)

        coordinator.async_request_refresh.assert_called_once()

    def test_turn_on_with_kwargs(self) -> None:
        """Test that turn_on with kwargs raises NotImplementedError."""
        coordinator = Mock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        with pytest.raises(NotImplementedError):
            switch.turn_on(extra_param="value", another_param=123)

    def test_turn_off_with_kwargs(self) -> None:
        """Test that turn_off with kwargs raises NotImplementedError."""
        coordinator = Mock()
        entity_desc = SwitchEntityDescription(key="idokep", name="Test Switch")
        switch = IdokepSwitch(coordinator, entity_desc)

        with pytest.raises(NotImplementedError):
            switch.turn_off(extra_param="value", another_param=123)
