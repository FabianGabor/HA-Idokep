"""Időkép API Client."""

from __future__ import annotations

import datetime
import re
import socket
from typing import Any

import aiohttp
import async_timeout
from bs4 import BeautifulSoup, Tag

from .const import LOGGER


class IdokepApiClientError(Exception):
    """Exception to indicate a general API error."""


class IdokepApiClientCommunicationError(
    IdokepApiClientError,
):
    """Exception to indicate a communication error."""


class IdokepApiClientAuthenticationError(
    IdokepApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise IdokepApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class IdokepApiClient:
    """API client for scraping Időkép weather data."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="get",
            url="https://jsonplaceholder.typicode.com/posts/1",
        )

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise IdokepApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise IdokepApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise IdokepApiClientError(
                msg,
            ) from exception

    def _map_condition(self, condition: str) -> str:
        """Map Hungarian condition to Home Assistant standard condition."""
        mapping = {
            "napos": "sunny",
            "derült": "sunny",
            "borult": "cloudy",
            "erősen felhős": "cloudy",
            "közepesen felhős": "partlycloudy",
            "gyengén felhős": "partlycloudy",
            "zivatar": "lightning-rainy",
            "zápor": "rainy",
            "szitálás": "rainy",
            "gyenge eső": "rainy",
            "eső": "rainy",
            "eső viharos széllel": "rainy",
            "köd": "fog",
            "párás": "fog",
            "pára": "fog",
            "villámlás": "lightning",
            "erős eső": "pouring",
            "jégeső": "hail",
            "havazás": "snowy",
            "hószállingózás": "snowy",
            "havas eső": "snowy-rainy",
            "fagyott eső": "snowy-rainy",
            "szeles": "windy",
        }
        return mapping.get(condition.lower(), "unknown")

    async def async_get_weather_data(self, location: str) -> dict[str, Any]:
        """
        Scrape as much weather data as possible for the given location from Időkép.

        Returns a dictionary with temperature, condition, and any other available data.
        """
        url = f"https://www.idokep.hu/idojaras/{location}"
        forecast_url = f"https://www.idokep.hu/elorejelzes/{location}"
        daily_url = f"https://www.idokep.hu/30napos/{location}"
        data = {}
        try:
            data.update(await self._scrape_current_weather(url))
            data.update(await self._scrape_hourly_forecast(forecast_url))
            data.update(await self._scrape_daily_forecast(daily_url))
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping Idokep: %s", exc)
        return data

    async def _scrape_current_weather(self, url: str) -> dict:
        result = {}
        try:
            async with async_timeout.timeout(10), self._session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Temperature
                temp_div = soup.find("div", class_="ik current-temperature")
                if isinstance(temp_div, Tag):
                    match = re.search(r"(-?\d+)[^\d]*C", temp_div.text)
                    if match:
                        result["temperature"] = int(match.group(1))

                # Weather condition
                cond_div = soup.find("div", class_="ik current-weather")
                if isinstance(cond_div, Tag):
                    condition = cond_div.text.strip()
                    result["condition"] = self._map_condition(condition)

                # Weather title (e.g., 'Jelenleg')
                title_div = soup.find("div", class_="ik current-weather-title")
                if isinstance(title_div, Tag):
                    result["weather_title"] = title_div.text.strip()

                # Sunrise and sunset
                result.update(self._parse_sunrise_sunset(soup))

                # Short forecast text
                short_forecast = self._parse_short_forecast(soup)
                if short_forecast:
                    result["short_forecast"] = short_forecast

        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping current weather: %s", exc)
        return result

    def _extract_time_from_text(
        self,
        label: str,
        div: Tag,
        today: datetime.date,
        local_tz: datetime.tzinfo,
        text: str,
    ) -> str | None:
        if label in text:
            text = div.get_text(strip=True)
            match = re.search(rf"{label}\s*([0-9]{{1,2}}:[0-9]{{2}})", text)
            if match:
                time_str = match.group(1)
                hour, minute = map(int, time_str.split(":"))
                dt = datetime.datetime.combine(
                    today, datetime.time(hour, minute, tzinfo=local_tz)
                )
                return dt.isoformat()
        return None

    def _parse_sunrise_sunset(self, soup: BeautifulSoup) -> dict:
        """Extract sunrise and sunset times from the soup."""
        result = {}
        today = datetime.datetime.now(tz=datetime.UTC).date()
        local_tz = datetime.datetime.now().astimezone().tzinfo or datetime.UTC
        for div in soup.find_all("div"):
            if not isinstance(div, Tag):
                continue
            img = div.find("img") if hasattr(div, "find") else None
            if img and isinstance(img, Tag):
                alt = str(img.attrs.get("alt", ""))

                sunrise_iso = self._extract_time_from_text(
                    "Napkelte", div, today, local_tz, alt
                )
                if sunrise_iso is not None:
                    result["sunrise"] = sunrise_iso

                sunset_iso = self._extract_time_from_text(
                    "Napnyugta", div, today, local_tz, alt
                )
                if sunset_iso is not None:
                    result["sunset"] = sunset_iso
        return result

    def _parse_short_forecast(self, soup: BeautifulSoup) -> str | None:
        """Extract short forecast text from the soup."""
        for div in soup.find_all("div", class_="pt-2"):
            if not isinstance(div, Tag):
                continue
            if not div.find("img") and not div.find("button"):
                text = div.get_text(strip=True)
                if text and "Napkelte" not in text and "Napnyugta" not in text:
                    return text
        return None

    async def _scrape_hourly_forecast(self, forecast_url: str) -> dict:
        result = {}
        try:
            async with (
                async_timeout.timeout(10),
                self._session.get(forecast_url) as response,
            ):
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                forecast = []
                now = datetime.datetime.now(tz=datetime.UTC)
                current_hour = now.hour
                current_date = now.date()
                hourly_cards = soup.find_all(
                    "div", class_="ik new-hourly-forecast-card"
                )
                for card in hourly_cards:
                    if not isinstance(card, Tag):
                        continue
                    hour_div = (
                        card.find("div", class_="ik new-hourly-forecast-hour")
                        if isinstance(card, Tag)
                        else None
                    )
                    temp_div = (
                        card.find("div", class_="ik tempValue")
                        if isinstance(card, Tag)
                        else None
                    )
                    icon_container = (
                        card.find("div", class_="forecast-icon-container")
                        if isinstance(card, Tag)
                        else None
                    )
                    icon_a = (
                        icon_container.find("a")
                        if icon_container and isinstance(icon_container, Tag)
                        else None
                    )
                    condition = None
                    if icon_a and isinstance(icon_a, Tag):
                        condition_val = icon_a.get("data-bs-content")
                        if isinstance(condition_val, str):
                            condition = self._map_condition(condition_val)
                    if (
                        hour_div
                        and temp_div
                        and isinstance(hour_div, Tag)
                        and isinstance(temp_div, Tag)
                    ):
                        hour = hour_div.text.strip()
                        temp_a = (
                            temp_div.find("a") if isinstance(temp_div, Tag) else None
                        )
                        temp = (
                            int(temp_a.text.strip())
                            if temp_a
                            and isinstance(temp_a, Tag)
                            and temp_a.text.strip().isdigit()
                            else None
                        )
                        hour_int = int(hour.split(":")[0])
                        minute_int = int(hour.split(":")[1]) if ":" in hour else 0
                        forecast_date = current_date
                        if hour_int < current_hour:
                            forecast_date = current_date + datetime.timedelta(days=1)
                        dt = datetime.datetime.combine(
                            forecast_date, datetime.time(hour_int, minute_int)
                        )
                        dt_iso = dt.isoformat()
                        forecast_item = {
                            "datetime": dt_iso,
                            "temperature": temp,
                            "condition": condition,
                        }
                        forecast.append(forecast_item)
                if forecast:
                    result["forecast"] = forecast[:24]
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping hourly forecast: %s", exc)
        return result

    async def _scrape_daily_forecast(self, daily_url: str) -> dict:
        def extract_temp(div: Tag, class_name: str) -> int | None:
            temp_div = div.find("div", class_=class_name)
            if temp_div and isinstance(temp_div, Tag):
                temp_a = temp_div.find("a")
                if temp_a and isinstance(temp_a, Tag):
                    match = re.search(r"(-?\d+)", temp_a.text)
                    if match:
                        return int(match.group(1))
            return None

        def extract_condition(col: Tag) -> str | None:
            icon_alert = col.find("div", class_="ik dfIconAlert")
            if icon_alert and isinstance(icon_alert, Tag):
                a_tag = icon_alert.find("a")
                if a_tag and isinstance(a_tag, Tag):
                    popover = a_tag.get("data-bs-content")
                    if isinstance(popover, str):
                        match = re.search(
                            r"popover-icon' src='[^']+'>([^<]+)<", popover
                        )
                        if match:
                            return self._map_condition(match.group(1).strip())
                        text_match = re.search(
                            r"popover-icon' src='[^']+'>([^<]+)", popover
                        )
                        if text_match:
                            return self._map_condition(text_match.group(1).strip())
            return None

        def extract_precipitation(col: Tag) -> int:
            precip_span = col.find("span", class_="ik mm")
            if precip_span and isinstance(precip_span, Tag):
                precip_text = precip_span.text.strip()
                if precip_text:
                    match = re.search(r"(\d+)", precip_text)
                    if match:
                        return int(match.group(1))
            return 0

        result = {}
        try:
            async with (
                async_timeout.timeout(10),
                self._session.get(daily_url) as response,
            ):
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                daily_forecast = []
                daily_cols = soup.find_all("div", class_="ik dailyForecastCol")
                today = datetime.datetime.now(tz=datetime.UTC).date()
                for i, col in enumerate(daily_cols):
                    if not isinstance(col, Tag):
                        continue
                    forecast_date = today + datetime.timedelta(days=i)
                    min_temp = extract_temp(col, "ik min")
                    max_temp = extract_temp(col, "ik max")
                    condition = extract_condition(col)
                    precipitation = extract_precipitation(col)

                    daily_forecast.append(
                        {
                            "datetime": str(forecast_date),
                            "temperature": max_temp,
                            "templow": min_temp,
                            "condition": condition,
                            "precipitation": precipitation,
                        }
                    )
                if daily_forecast:
                    result["daily_forecast"] = daily_forecast
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping 30-napos Idokep: %s", exc)
        return result
