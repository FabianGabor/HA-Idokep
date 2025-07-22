"""Binary sensor platform for idokep."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import IdokepEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import IdokepDataUpdateCoordinator
    from .data import IdokepConfigEntry

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="idokep_connectivity",
        translation_key="idokep_connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="storm_expected_1h",
        translation_key="storm_expected_1h",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:weather-lightning",
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        IdokepBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IdokepBinarySensor(IdokepEntity, BinarySensorEntity):
    """idokep binary_sensor class."""

    @property
    def has_entity_name(self) -> bool:
        """Return True if the entity has a name."""
        return True

    def __init__(
        self,
        coordinator: IdokepDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        # Set unique_id for entity persistence after restart
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self.entity_description.key == "storm_expected_1h":
            return self._check_storm_expected_next_hour()
        if self.entity_description.key == "idokep_connectivity":
            return self._check_data_fresh()
        return False

    def _check_data_fresh(self) -> bool:
        """Check if data is fresh and API updated successfully."""
        # Check if coordinator has recent successful update
        if not self.coordinator.last_update_success:
            return False

        # Check if we have actual data
        if not self.coordinator.data:
            return False

        # Check essential data fields are present
        essential_fields = ["temperature", "condition"]
        return all(field in self.coordinator.data for field in essential_fields)

    def _check_storm_expected_next_hour(self) -> bool:
        """Check if storm is expected in the next hour."""
        now = datetime.datetime.now(datetime.UTC)
        next_hour = now + datetime.timedelta(hours=1)

        for forecast in self.coordinator.data.get("hourly_forecast", []):
            if forecast.get("condition") and "Zivatar" in forecast.get("condition", ""):
                try:
                    forecast_dt = datetime.datetime.fromisoformat(
                        forecast.get("datetime", "")
                    )
                    # Make timezone-aware if needed
                    if forecast_dt.tzinfo is None:
                        forecast_dt = forecast_dt.replace(tzinfo=datetime.UTC)

                    # Check if forecast is within the next hour
                    if now <= forecast_dt <= next_hour:
                        return True
                except (ValueError, TypeError):
                    # Skip invalid datetime entries
                    continue
        return False
