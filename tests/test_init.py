"""Unit tests for the Időkép integration __init__.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.idokep import (
    PLATFORMS,
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.idokep.const import DOMAIN


class TestIdokepInit:
    """Test cases for Időkép integration initialization."""

    def test_platforms_constant(self) -> None:
        """Test that PLATFORMS constant is correctly defined."""
        expected_platforms = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.WEATHER]
        assert expected_platforms == PLATFORMS

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(self) -> None:
        """Test successful setup of config entry."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.domain = DOMAIN
        mock_entry.entry_id = "test_entry_id"
        mock_entry.data = {"location": "Budapest"}

        # Mock runtime data assignment
        mock_entry.runtime_data = None
        mock_entry.async_on_unload = Mock()
        mock_entry.add_update_listener = Mock(return_value="listener")

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        # Mock API client
        mock_client = Mock()

        # Mock integration
        mock_integration = Mock()

        with (
            patch(
                "custom_components.idokep.IdokepDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch(
                "custom_components.idokep.async_get_clientsession"
            ) as mock_get_session,
            patch(
                "custom_components.idokep.async_get_loaded_integration"
            ) as mock_get_integration,
            patch("custom_components.idokep.IdokepApiClient") as mock_api_client_class,
            patch("custom_components.idokep.IdokepData") as mock_data_class,
        ):
            # Configure mocks
            mock_coordinator_class.return_value = mock_coordinator
            mock_get_session.return_value = "session"
            mock_get_integration.return_value = mock_integration
            mock_api_client_class.return_value = mock_client
            mock_data_class.return_value = "data"

            # Mock forward_entry_setups
            mock_hass.config_entries.async_forward_entry_setups = AsyncMock(
                return_value=True
            )

            # Call the function
            result = await async_setup_entry(mock_hass, mock_entry)

            # Assertions
            assert result is True
            mock_coordinator_class.assert_called_once()
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_entry, PLATFORMS
            )
            mock_entry.async_on_unload.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_entry_coordinator_failure(self) -> None:
        """Test setup failure when coordinator first refresh fails."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.domain = DOMAIN
        mock_entry.data = {"location": "Budapest"}

        # Mock coordinator that fails
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock(
            side_effect=Exception("Coordinator failure")
        )

        with (
            patch(
                "custom_components.idokep.IdokepDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch("custom_components.idokep.async_get_clientsession"),
            patch("custom_components.idokep.async_get_loaded_integration"),
            patch("custom_components.idokep.IdokepApiClient"),
            patch("custom_components.idokep.IdokepData"),
        ):
            mock_coordinator_class.return_value = mock_coordinator

            # Call the function and expect exception
            with pytest.raises(Exception, match="Coordinator failure"):
                await async_setup_entry(mock_hass, mock_entry)

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(self) -> None:
        """Test successful unloading of config entry."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)

        # Mock unload_platforms
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        # Call the function
        result = await async_unload_entry(mock_hass, mock_entry)

        # Assertions
        assert result is True
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry, PLATFORMS
        )

    @pytest.mark.asyncio
    async def test_async_unload_entry_failure(self) -> None:
        """Test unloading failure."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)

        # Mock unload_platforms to return False
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        # Call the function
        result = await async_unload_entry(mock_hass, mock_entry)

        # Assertions
        assert result is False

    @pytest.mark.asyncio
    async def test_async_reload_entry(self) -> None:
        """Test reloading of config entry."""
        # Mock dependencies
        mock_hass = Mock(spec=HomeAssistant)
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry_id"

        # Mock reload
        mock_hass.config_entries.async_reload = AsyncMock()

        # Call the function
        await async_reload_entry(mock_hass, mock_entry)

        # Assertions
        mock_hass.config_entries.async_reload.assert_called_once_with("test_entry_id")
