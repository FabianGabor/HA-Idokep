"""IdokepEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import IdokepDataUpdateCoordinator


class IdokepEntity(CoordinatorEntity[IdokepDataUpdateCoordinator]):
    """IdokepEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: IdokepDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            name="Időkép",  # Add device name
        )
