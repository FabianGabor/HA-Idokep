"""Sample API Client."""

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
        data = {}
        try:
            async with async_timeout.timeout(10), self._session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Temperature
                temp_div = soup.find("div", class_="ik current-temperature")
                if temp_div:
                    match = re.search(r"(-?\d+)[^\d]*C", temp_div.text)
                    if match:
                        data["temperature"] = int(match.group(1))

                # Weather condition
                cond_div = soup.find("div", class_="ik current-weather")
                if cond_div:
                    condition = cond_div.text.strip()
                    data["condition"] = self._map_condition(condition)

                # Weather title (e.g., 'Jelenleg')
                title_div = soup.find("div", class_="ik current-weather-title")
                if title_div:
                    data["weather_title"] = title_div.text.strip()

                # Sunrise and sunset (look for divs with img alt="Napkelte" or "Napnyugta")
                today = datetime.datetime.now().date()
                local_tz = datetime.datetime.now().astimezone().tzinfo
                for div in soup.find_all("div"):
                    img = div.find("img") if hasattr(div, "find") else None
                    if img and isinstance(img, Tag):
                        alt = img.attrs.get("alt", "")
                        if "Napkelte" in alt:
                            text = div.get_text(strip=True)
                            match = re.search(r"Napkelte\s*([0-9]{1,2}:[0-9]{2})", text)
                            if match:
                                sunrise_time = match.group(1)
                                hour, minute = map(int, sunrise_time.split(":"))
                                dt = datetime.datetime.combine(today, datetime.time(hour, minute, tzinfo=local_tz))
                                data["sunrise"] = dt.isoformat()
                                LOGGER.debug("Parsed sunrise ISO: %s (type: %s)", data["sunrise"], type(data["sunrise"]))
                        if "Napnyugta" in alt:
                            text = div.get_text(strip=True)
                            match = re.search(r"Napnyugta\s*([0-9]{1,2}:[0-9]{2})", text)
                            if match:
                                sunset_time = match.group(1)
                                hour, minute = map(int, sunset_time.split(":"))
                                dt = datetime.datetime.combine(today, datetime.time(hour, minute, tzinfo=local_tz))
                                data["sunset"] = dt.isoformat()
                                LOGGER.debug("Parsed sunset ISO: %s (type: %s)", data["sunset"], type(data["sunset"]))

                # Short forecast text (skip divs with img or button)
                for div in soup.find_all("div", class_="pt-2"):
                    if not div.find("img") and not div.find("button"):
                        text = div.get_text(strip=True)
                        if (
                            text
                            and "Napkelte" not in text
                            and "Napnyugta" not in text
                            and len(text) > 3
                        ):
                            data["short_forecast"] = text
                            break

            # Fetch hourly forecast from forecast_url
            async with async_timeout.timeout(10), self._session.get(forecast_url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                forecast = []
                now = datetime.datetime.now()
                current_hour = now.hour
                current_date = now.date()
                hourly_cards = soup.find_all(
                    "div", class_="ik new-hourly-forecast-card"
                )
                for card in hourly_cards:
                    hour_div = card.find(
                        "div", class_="ik new-hourly-forecast-hour"
                    )
                    temp_div = card.find("div", class_="ik tempValue")
                    icon_a = card.find(
                        "div", class_="forecast-icon-container"
                    ).find("a")
                    wind_div = card.find("div", class_="hourly-wind")
                    wind_bearing = None
                    wind_speed = None
                    condition = None
                    if icon_a and icon_a.has_attr("data-bs-content"):
                        condition = icon_a["data-bs-content"]
                    if wind_div:
                        wind_a = wind_div.find("a")
                        wind_icon = (
                            wind_a.find("div", class_="ik wind") if wind_a else None
                        )
                        if wind_icon and wind_icon.has_attr("class"):
                            for c in wind_icon["class"]:
                                if c.startswith("r") and c[1:].isdigit():
                                    wind_bearing = int(c[1:])
                    if hour_div and temp_div:
                        hour = hour_div.text.strip()
                        temp_a = temp_div.find("a")
                        temp = (
                            int(temp_a.text.strip())
                            if temp_a and temp_a.text.strip().isdigit()
                            else None
                        )
                        # Build ISO datetime for forecast
                        hour_int = int(hour.split(":")[0])
                        minute_int = int(hour.split(":")[1]) if ":" in hour else 0
                        forecast_date = current_date
                        if hour_int < current_hour:
                            forecast_date = current_date + datetime.timedelta(
                                days=1
                            )
                        dt = datetime.datetime.combine(
                            forecast_date, datetime.time(hour_int, minute_int)
                        )
                        dt_iso = dt.isoformat()
                        forecast_item = {
                            "datetime": dt_iso,
                            "temperature": temp,
                            "condition": self._map_condition(condition)
                            if condition
                            else None,
                        }
                        forecast.append(forecast_item)
                if forecast:
                    data["forecast"] = forecast[:24]  # Limit to 24 hours

                LOGGER.debug("Napkelte: %s", data.get("sunrise"))
                LOGGER.debug("Napnyugta: %s", data.get("sunset"))
                LOGGER.debug("Short forecast: %s", data.get("short_forecast"))
                LOGGER.debug("Hourly forecast: %s", data["forecast"])

            # --- 30-day daily forecast ---
            daily_url = f"https://www.idokep.hu/30napos/{location}"
            try:
                async with async_timeout.timeout(10), self._session.get(daily_url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    daily_forecast = []
                    daily_cols = soup.find_all("div", class_="ik dailyForecastCol")
                    today = datetime.datetime.now().date()
                    for i, col in enumerate(daily_cols):
                        # Get min/max temps
                        min_temp = None
                        max_temp = None
                        minmax_container = col.find("div", class_="ik min-max-container") if hasattr(col, "find") else None
                        if minmax_container:
                            max_div = minmax_container.find("div", class_="ik max") if hasattr(minmax_container, "find") else None
                            min_div = minmax_container.find("div", class_="ik min") if hasattr(minmax_container, "find") else None
                            if max_div:
                                max_a = max_div.find("a") if hasattr(max_div, "find") else None
                                if isinstance(max_a, Tag):
                                    max_match = re.search(r"(-?\d+)", max_a.text)
                                    if max_match:
                                        max_temp = int(max_match.group(1))
                            if min_div:
                                min_a = min_div.find("a") if hasattr(min_div, "find") else None
                                if isinstance(min_a, Tag):
                                    min_match = re.search(r"(-?\d+)", min_a.text)
                                    if min_match:
                                        min_temp = int(min_match.group(1))
                        # Get condition from icon popover or fallback
                        condition = None
                        icon_alert = col.find("div", class_="ik dfIconAlert") if hasattr(col, "find") else None
                        if icon_alert:
                            a_tag = icon_alert.find("a") if hasattr(icon_alert, "find") else None
                            if a_tag and hasattr(a_tag, "get"):
                                popover = a_tag.get("data-bs-content", "")
                                match = re.search(r"popover-icon' src='[^']+'>([^<]+)<", popover)
                                if match:
                                    condition = self._map_condition(match.group(1).strip())
                                else:
                                    text_match = re.search(r"popover-icon' src='[^']+'>([^<]+)", popover)
                                    if text_match:
                                        condition = self._map_condition(text_match.group(1).strip())
                        # Build forecast date (today + i)
                        forecast_date = today + datetime.timedelta(days=i)
                        daily_forecast.append({
                            "datetime": str(forecast_date),
                            "temperature": max_temp,
                            "templow": min_temp,
                            "condition": condition,
                        })

                        LOGGER.debug("Daily forecast for %s: %s", forecast_date, daily_forecast[-1])

                    if daily_forecast:
                        data["daily_forecast"] = daily_forecast
            except Exception as exc:
                LOGGER.error("Error scraping 30-napos Idokep: %s", exc)

        except Exception as exc:
            LOGGER.error("Error scraping Idokep: %s", exc)
        return data
