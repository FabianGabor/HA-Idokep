"""Sensor platform for idokep."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import IdokepEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import IdokepDataUpdateCoordinator
    from .data import IdokepConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="temperature",
        name="Current Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="condition",
        name="Current Weather Condition",
        icon="mdi:weather-partly-cloudy",
    ),
    SensorEntityDescription(
        key="sunrise",
        name="Sunrise",
        icon="mdi:weather-sunset-up",
    ),
    SensorEntityDescription(
        key="sunset",
        name="Sunset",
        icon="mdi:weather-sunset-down",
    ),
    SensorEntityDescription(
        key="short_forecast",
        name="Short Forecast",
        icon="mdi:weather-cloudy-clock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
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
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
