"""Adds config flow for Idokep."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import IdokepApiClient
from .const import DOMAIN, LOGGER


class WeatherDataFetchError(ValueError):
    """Exception raised when weather data cannot be fetched for a given location."""

    def __init__(self, location: str) -> None:
        """Initialize WeatherDataFetchError with the given location."""
        msg = f"Could not fetch weather data for {location}"
        super().__init__(msg)


class IdokepFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_location(
                    location=user_input["location"],
                )
            except ValueError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            else:
                await self.async_set_unique_id(
                    unique_id=slugify(user_input["location"])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["location"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "location",
                        default=(user_input or {}).get("location", vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_location(self, location: str) -> None:
        """Validate location by scraping Idokep."""
        client = IdokepApiClient(
            session=async_create_clientsession(self.hass),
        )
        data = await client.async_get_weather_data(location)
        if not data or "temperature" not in data:
            raise WeatherDataFetchError(location)
