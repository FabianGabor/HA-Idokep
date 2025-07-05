"""Switch platform for idokep."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .entity import IdokepEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import IdokepDataUpdateCoordinator
    from .data import IdokepConfigEntry

ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="idokep",
        name="Integration Switch",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        IdokepSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IdokepSwitch(IdokepEntity, SwitchEntity):
    """idokep switch class."""

    def __init__(
        self,
        coordinator: IdokepDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get("title", "") == "foo"

    def turn_on(self, **_: Any) -> None:
        """Turn on the switch (sync version)."""
        # This method is abstract in ToggleEntity but deprecated
        # SwitchEntity should use async_turn_on instead
        raise NotImplementedError

    def turn_off(self, **_: Any) -> None:
        """Turn off the switch (sync version)."""
        # This method is abstract in ToggleEntity but deprecated
        # SwitchEntity should use async_turn_off instead
        raise NotImplementedError

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        # For now, just request a refresh as this is a demo switch
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        # For now, just request a refresh as this is a demo switch
        await self.coordinator.async_request_refresh()
