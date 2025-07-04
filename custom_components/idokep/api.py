"""Időkép API Client."""

from __future__ import annotations

import asyncio
import datetime
import re
import socket
from typing import Any

import aiohttp
import async_timeout
from bs4 import BeautifulSoup, Tag

try:
    import zoneinfo
except ImportError:
    zoneinfo = None

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

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(5):
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
            # Make all requests concurrently to reduce total time
            results = await asyncio.gather(
                self._scrape_current_weather(url),
                self._scrape_hourly_forecast(forecast_url),
                self._scrape_daily_forecast(daily_url),
                return_exceptions=True,
            )

            # Process results, skipping any that failed
            for result in results:
                if isinstance(result, dict):
                    data.update(result)
                elif isinstance(result, Exception):
                    LOGGER.warning("Failed to scrape some weather data: %s", result)

        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping Idokep: %s", exc)
        return data

    async def _scrape_current_weather(self, url: str) -> dict:
        result = {}
        try:
            async with async_timeout.timeout(5), self._session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Find all ik elements at once to reduce DOM traversal
                temp_div = soup.find("div", class_="ik current-temperature")
                cond_div = soup.find("div", class_="ik current-weather")
                title_div = soup.find("div", class_="ik current-weather-title")

                # Temperature
                if isinstance(temp_div, Tag):
                    match = re.search(r"(-?\d+)[^\d]*C", temp_div.text)
                    if match:
                        result["temperature"] = int(match.group(1))

                # Weather condition
                if isinstance(cond_div, Tag):
                    condition = cond_div.text.strip()
                    result["condition"] = self._map_condition(condition)
                    result["condition_hu"] = condition

                # Weather title (e.g., 'Jelenleg')
                if isinstance(title_div, Tag):
                    result["weather_title"] = title_div.text.strip()

                # Sunrise and sunset
                result.update(self._parse_sunrise_sunset(soup))

                # Short forecast text
                short_forecast = self._parse_short_forecast(soup)
                if short_forecast:
                    result["short_forecast"] = short_forecast

                # Extract current precipitation data
                precipitation_data = self._extract_current_precipitation(soup)
                if precipitation_data:
                    result["precipitation"] = precipitation_data.get("precipitation", 0)
                    result["precipitation_probability"] = precipitation_data.get(
                        "precipitation_probability", 0
                    )
                    LOGGER.debug("Precipitation data: %s", precipitation_data)

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
                LOGGER.debug(
                    "Extracted %s time: %s. Timezone: %s",
                    label,
                    dt.isoformat(),
                    local_tz,
                )
                return dt.isoformat()
        return None

    def _parse_sunrise_sunset(self, soup: BeautifulSoup) -> dict:
        """Extract sunrise and sunset times from the soup."""
        local_tz = (
            zoneinfo.ZoneInfo("Europe/Budapest")
            if zoneinfo is not None
            else datetime.timezone(datetime.timedelta(hours=2))
        )
        today = datetime.datetime.now(tz=local_tz).date()
        result = {}

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

    def _extract_hourly_precipitation_data(self, card: Tag) -> tuple[int, int]:
        """Extract precipitation probability and amount from hourly forecast card."""
        precipitation_probability = 0
        precipitation = 0

        # Extract precipitation probability
        rain_chance_div = card.find("div", class_="ik hourly-rain-chance")
        if rain_chance_div and isinstance(rain_chance_div, Tag):
            rain_a = rain_chance_div.find("a")
            if rain_a and isinstance(rain_a, Tag):
                rain_text = rain_a.text.strip()
                if rain_text.endswith("%"):
                    try:
                        precipitation_probability = int(rain_text[:-1])
                    except ValueError:
                        precipitation_probability = 0

        # Extract precipitation amount (from rainlevel classes)
        rainlevel_pattern = re.compile(r"ik rainlevel-\d+")
        rainlevel_divs = card.find_all("div", class_=rainlevel_pattern)
        if rainlevel_divs:
            for rainlevel_div in rainlevel_divs:
                if isinstance(rainlevel_div, Tag):
                    class_attr = rainlevel_div.get("class")
                    if class_attr:
                        class_list = (
                            class_attr if isinstance(class_attr, list) else [class_attr]
                        )
                        for class_name in class_list:
                            if isinstance(class_name, str) and class_name.startswith(
                                "rainlevel-"
                            ):
                                try:
                                    # Extract number from rainlevel-X class
                                    precip_match = re.search(
                                        r"rainlevel-(\d+)", class_name
                                    )
                                    if precip_match:
                                        precipitation = int(precip_match.group(1))
                                        break
                                except ValueError:
                                    continue

        return precipitation, precipitation_probability

    async def _scrape_hourly_forecast(self, forecast_url: str) -> dict:
        result = {}
        try:
            async with (
                async_timeout.timeout(5),
                self._session.get(forecast_url) as response,
            ):
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                forecast = []
                now = datetime.datetime.now(tz=datetime.UTC)
                current_hour = now.hour
                current_date = now.date()

                # Find all hourly cards at once
                hourly_cards = soup.find_all(
                    "div", class_="ik new-hourly-forecast-card"
                )

                for card in hourly_cards:
                    if not isinstance(card, Tag):
                        continue

                    # Find all child elements at once to minimize DOM traversal
                    hour_div = card.find("div", class_="ik new-hourly-forecast-hour")
                    temp_div = card.find("div", class_="ik tempValue")
                    icon_container = card.find("div", class_="forecast-icon-container")

                    condition = None
                    if icon_container and isinstance(icon_container, Tag):
                        icon_a = icon_container.find("a")
                        if icon_a and isinstance(icon_a, Tag):
                            condition_val = icon_a.get("data-bs-content")
                            if isinstance(condition_val, str):
                                condition = self._map_condition(condition_val)

                    # Extract precipitation data
                    precipitation, precipitation_probability = (
                        self._extract_hourly_precipitation_data(card)
                    )

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
                            "precipitation": precipitation,
                            "precipitation_probability": precipitation_probability,
                        }
                        forecast.append(forecast_item)
                if forecast:
                    result["hourly_forecast"] = forecast[:24]
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping hourly forecast: %s", exc)
        return result

    def _extract_daily_temperature(self, col: Tag, class_name: str) -> int | None:
        """Extract temperature from daily forecast column."""
        temp_div = col.find("div", class_=class_name)
        if temp_div and isinstance(temp_div, Tag):
            temp_a = temp_div.find("a")
            if temp_a and isinstance(temp_a, Tag):
                match = re.search(r"(-?\d+)", temp_a.text)
                if match:
                    return int(match.group(1))
        return None

    def _extract_daily_condition(self, col: Tag) -> str | None:
        """Extract weather condition from daily forecast column."""
        icon_alert = col.find("div", class_="ik dfIconAlert")
        if not (icon_alert and isinstance(icon_alert, Tag)):
            return None

        a_tag = icon_alert.find("a")
        if not (a_tag and isinstance(a_tag, Tag)):
            return None

        popover = a_tag.get("data-bs-content")
        if not isinstance(popover, str):
            return None

        # Try detailed match first
        match = re.search(r"popover-icon' src='[^']+'>([^<]+)<", popover)
        if match:
            return self._map_condition(match.group(1).strip())

        # Try simpler match as fallback
        text_match = re.search(r"popover-icon' src='[^']+'>([^<]+)", popover)
        if text_match:
            return self._map_condition(text_match.group(1).strip())

        return None

    def _extract_daily_precipitation(self, col: Tag) -> int:
        """Extract precipitation from daily forecast column."""
        precip_span = col.find("span", class_="ik mm")
        if precip_span and isinstance(precip_span, Tag):
            precip_text = precip_span.text.strip()
            if precip_text:
                match = re.search(r"(\d+)", precip_text)
                if match:
                    return int(match.group(1))
        return 0

    def _extract_daily_precipitation_probability(self, col: Tag) -> int:
        """Extract precipitation probability from daily forecast column."""
        # Look for percentage values in various elements
        for element in col.find_all(["span", "div", "a"], string=re.compile(r"\d+%")):
            if isinstance(element, Tag):
                percent_text = element.text.strip()
                if percent_text.endswith("%"):
                    try:
                        return int(percent_text[:-1])
                    except ValueError:
                        continue

        # Look for data attributes containing precipitation probability
        for element in col.find_all(["a", "div"], attrs={"data-bs-content": True}):
            if isinstance(element, Tag):
                content = element.get("data-bs-content")
                if isinstance(content, str) and (
                    "csapadék" in content.lower() or "precipitation" in content.lower()
                ):
                    percent_match = re.search(r"(\d+)%", content)
                    if percent_match:
                        try:
                            return int(percent_match.group(1))
                        except ValueError:
                            continue

        return 0

    async def _scrape_daily_forecast(self, daily_url: str) -> dict:
        result = {}
        try:
            async with (
                async_timeout.timeout(5),
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
                    min_temp = self._extract_daily_temperature(col, "ik min")
                    max_temp = self._extract_daily_temperature(col, "ik max")
                    condition = self._extract_daily_condition(col)
                    precipitation = self._extract_daily_precipitation(col)
                    precipitation_probability = (
                        self._extract_daily_precipitation_probability(col)
                    )

                    daily_forecast.append(
                        {
                            "datetime": str(forecast_date),
                            "temperature": max_temp,
                            "templow": min_temp,
                            "condition": condition,
                            "precipitation": precipitation,
                            "precipitation_probability": precipitation_probability,
                        }
                    )
                if daily_forecast:
                    result["daily_forecast"] = daily_forecast
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping 30-napos Idokep: %s", exc)
        return result

    def _extract_current_precipitation(self, soup: BeautifulSoup) -> dict:
        """Extract current precipitation data from the main weather page."""
        result = {"precipitation": 0, "precipitation_probability": 0}

        # Look for precipitation probability in various locations
        for element in soup.find_all(["div", "span"], string=re.compile(r"\d+%")):
            if isinstance(element, Tag):
                parent = element.parent
                if parent and isinstance(parent, Tag):
                    parent_text = parent.get_text().lower()
                    if any(
                        keyword in parent_text
                        for keyword in ["csapadék", "eső", "precipitation"]
                    ):
                        percent_match = re.search(r"(\d+)%", element.text)
                        if percent_match:
                            result["precipitation_probability"] = int(
                                percent_match.group(1)
                            )
                            break

        # Look for precipitation amount indicators
        for element in soup.find_all(["div", "span"], string=re.compile(r"\d+\s*mm")):
            if isinstance(element, Tag):
                mm_match = re.search(r"(\d+)\s*mm", element.text)
                if mm_match:
                    result["precipitation"] = int(mm_match.group(1))
                    break

        return result
