"""
Custom integration to integrate idokep with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/integration_blueprint
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import IdokepApiClient
from .const import DOMAIN, LOGGER
from .coordinator import IdokepDataUpdateCoordinator
from .data import IdokepData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IdokepConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.WEATHER,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = IdokepDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=5),
        config_entry=entry,
    )
    entry.runtime_data = IdokepData(
        client=IdokepApiClient(
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # Ensure data is available before creating entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
