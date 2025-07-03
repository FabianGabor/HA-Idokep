"""Custom types for idokep."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import IdokepApiClient
    from .coordinator import IdokepDataUpdateCoordinator


type IdokepConfigEntry = ConfigEntry[IdokepData]


@dataclass
class IdokepData:
    """Data for the Idokep integration."""

    client: IdokepApiClient
    coordinator: IdokepDataUpdateCoordinator
    integration: Integration
