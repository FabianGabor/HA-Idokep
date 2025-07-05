"""Sensor platform for idokep."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from .entity import IdokepEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import IdokepDataUpdateCoordinator
    from .data import IdokepConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="condition",
        translation_key="condition",
        icon="mdi:weather-partly-cloudy",
    ),
    SensorEntityDescription(
        key="condition_hu",
        translation_key="condition_hu",
        icon="mdi:weather-partly-cloudy",
    ),
    SensorEntityDescription(
        key="sunrise",
        translation_key="sunrise",
        icon="mdi:weather-sunset-up",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="sunset",
        translation_key="sunset",
        icon="mdi:weather-sunset-down",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="short_forecast",
        translation_key="short_forecast",
        icon="mdi:weather-cloudy-clock",
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        IdokepSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IdokepSensor(IdokepEntity, SensorEntity):
    """Idokep Sensor class."""

    @property
    def has_entity_name(self) -> bool:
        """Return True if the entity has a name."""
        return True

    def __init__(
        self,
        coordinator: IdokepDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def native_value(self) -> str | int | float | datetime | None:
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if (
            self.entity_description.device_class == SensorDeviceClass.TIMESTAMP
            and isinstance(value, str)
        ):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return value
