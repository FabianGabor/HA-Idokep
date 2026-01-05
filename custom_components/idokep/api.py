"""Refactored Időkép API Client with improved separation of concerns."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import re
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import aiohttp
import async_timeout
from bs4 import BeautifulSoup, Tag

try:
    import zoneinfo
except ImportError:
    zoneinfo = None

from .const import LOGGER


@dataclass
class WeatherData:
    """Structured weather data."""

    temperature: int | None = None
    condition: str | None = None
    condition_hu: str | None = None
    weather_title: str | None = None
    sunrise: str | None = None
    sunset: str | None = None
    short_forecast: str | None = None
    precipitation: int = 0
    precipitation_probability: int = 0


@dataclass
class HourlyForecastItem:
    """Single hourly forecast item."""

    datetime: str
    temperature: int | None
    condition: str | None
    precipitation: int = 0
    precipitation_probability: int = 0


@dataclass
class DailyForecastItem:
    """Single daily forecast item."""

    datetime: str
    temperature: int | None
    templow: int | None
    condition: str | None
    precipitation: int = 0
    precipitation_probability: int = 0


# Configuration and constants
class IdokepConfig:
    """Configuration for Időkép API."""

    BASE_URL = "https://www.idokep.hu"
    TIMEOUT = 5

    @classmethod
    def get_current_weather_url(cls, location: str) -> str:
        """Get current weather URL for location."""
        return f"{cls.BASE_URL}/idojaras/{location}"

    @classmethod
    def get_hourly_forecast_url(cls, location: str) -> str:
        """Get hourly forecast URL for location."""
        return f"{cls.BASE_URL}/elorejelzes/{location}"

    @classmethod
    def get_daily_forecast_url(cls, location: str) -> str:
        """Get daily forecast URL for location."""
        return f"{cls.BASE_URL}/30napos/{location}"


# Exception classes remain the same
class IdokepApiClientError(Exception):
    """Exception to indicate a general API error."""


class IdokepApiClientCommunicationError(IdokepApiClientError):
    """Exception to indicate a communication error."""


class IdokepApiClientAuthenticationError(IdokepApiClientError):
    """Exception to indicate an authentication error."""


class IdokepApiClientConnectivityError(IdokepApiClientError):
    """Exception to indicate no internet connectivity."""


# Weather condition mapper
class WeatherConditionMapper:
    """Maps Hungarian weather conditions to Home Assistant standards."""

    _CONDITION_MAPPING: ClassVar[dict[str, str]] = {
        "napos": "sunny",
        "derült": "sunny",
        "borult": "cloudy",
        "erősen felhős": "cloudy",
        "közepesen felhős": "partlycloudy",
        "gyengén felhős": "partlycloudy",
        "száraz zivatar": "lightning",
        "villámlás": "lightning",
        "zivatar": "lightning-rainy",
        "zápor": "rainy",
        "szitálás": "rainy",
        "gyenge eső": "rainy",
        "eső": "rainy",
        "eső viharos széllel": "rainy",
        "köd": "fog",
        "ködös": "fog",
        "ködszitálás": "fog",
        "párás": "fog",
        "pára": "fog",
        "erős eső": "pouring",
        "jégeső": "hail",
        "havazás": "snowy",
        "hószállingózás": "snowy",
        "havas eső": "snowy-rainy",
        "fagyott eső": "snowy-rainy",
        "szeles": "windy",
    }

    @classmethod
    def map_condition(cls, condition: str) -> str:
        """Map Hungarian condition to Home Assistant standard condition."""
        return cls._CONDITION_MAPPING.get(condition.lower(), "unknown")


# Time utilities
class TimeUtils:
    """Utilities for time handling."""

    @staticmethod
    def get_local_timezone() -> datetime.tzinfo:
        """Get Budapest timezone."""
        return (
            zoneinfo.ZoneInfo("Europe/Budapest")
            if zoneinfo is not None
            else datetime.timezone(datetime.timedelta(hours=2))
        )

    @staticmethod
    def extract_time_from_text(
        label: str,
        text: str,
        today: datetime.date,
        local_tz: datetime.tzinfo,
    ) -> str | None:
        """Extract time from text and convert to ISO format."""
        if label in text:
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


# HTTP client wrapper
class HttpClient:
    """HTTP client with error handling."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize HTTP client."""
        self._session = session

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the underlying session."""
        return self._session

    async def check_connectivity(self, host: str = "www.idokep.hu") -> bool:
        """Check if the host is reachable."""
        try:
            async with (
                async_timeout.timeout(3),
                self._session.get(f"https://{host}", ssl=False, allow_redirects=False),
            ):
                # We just need to check if we can connect, any response is fine
                return True
        except (aiohttp.ClientError, TimeoutError, socket.gaierror, OSError):
            return False

    async def get_html(self, url: str) -> str:
        """Get HTML content from URL with error handling."""
        try:
            async with (
                async_timeout.timeout(IdokepConfig.TIMEOUT),
                self._session.get(url) as response,
            ):
                response.raise_for_status()
                return await response.text()
        except TimeoutError as exception:
            msg = f"Timeout error fetching {url} - {exception}"
            raise IdokepApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching {url} - {exception}"
            raise IdokepApiClientCommunicationError(msg) from exception


# Abstract base for parsers
class WeatherParser(ABC):
    """Abstract base class for weather data parsers."""

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Parse weather data from BeautifulSoup object."""


# Specific parser implementations
class CurrentWeatherParser(WeatherParser):
    """Parser for current weather data."""

    def parse(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Parse current weather data."""
        result = {}

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
            result["condition"] = WeatherConditionMapper.map_condition(condition)
            result["condition_hu"] = condition

        # Weather title
        title_div = soup.find("div", class_="ik current-weather-title")
        if isinstance(title_div, Tag):
            result["weather_title"] = title_div.text.strip()

        # Sunrise and sunset
        result.update(self.parse_sunrise_sunset(soup))

        # Short forecast
        short_forecast = self.parse_short_forecast(soup)
        if short_forecast:
            result["short_forecast"] = short_forecast

        # Precipitation
        precipitation_data = self.extract_current_precipitation(soup)
        if precipitation_data:
            result["precipitation"] = precipitation_data.get("precipitation", 0)
            result["precipitation_probability"] = precipitation_data.get(
                "precipitation_probability", 0
            )

        return result

    def parse_sunrise_sunset(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract sunrise and sunset times."""
        local_tz = TimeUtils.get_local_timezone()
        today = datetime.datetime.now(tz=local_tz).date()
        result = {}

        for div in soup.find_all("div"):
            if not isinstance(div, Tag):
                continue
            img = div.find("img")
            if img and isinstance(img, Tag):
                alt = str(img.attrs.get("alt", ""))

                # Check if this div contains sunrise or sunset info
                if "Napkelte" in alt or "Napnyugta" in alt:
                    # Get the text content of the div which contains the time
                    div_text = div.get_text(strip=True)

                    if "Napkelte" in alt:
                        sunrise_iso = TimeUtils.extract_time_from_text(
                            "Napkelte", div_text, today, local_tz
                        )
                        if sunrise_iso:
                            result["sunrise"] = sunrise_iso

                    if "Napnyugta" in alt:
                        sunset_iso = TimeUtils.extract_time_from_text(
                            "Napnyugta", div_text, today, local_tz
                        )
                        if sunset_iso:
                            result["sunset"] = sunset_iso

        return result

    def parse_short_forecast(self, soup: BeautifulSoup) -> str | None:
        """Extract short forecast text."""
        # First try the new structure with current-weather-short-desc class
        short_desc_div = soup.find("div", class_="current-weather-short-desc")
        if isinstance(short_desc_div, Tag):
            text = short_desc_div.get_text(strip=True)
            if text:
                return text

        # Fallback to old structure for backwards compatibility
        for div in soup.find_all("div", class_="pt-2"):
            if not isinstance(div, Tag):
                continue
            if not div.find("img") and not div.find("button"):
                text = div.get_text(strip=True)
                if text and "Napkelte" not in text and "Napnyugta" not in text:
                    return text
        return None

    def extract_current_precipitation(self, soup: BeautifulSoup) -> dict[str, int]:
        """Extract current precipitation data."""
        result = {"precipitation": 0, "precipitation_probability": 0}

        # Look for precipitation probability
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

        # Look for precipitation amount
        for element in soup.find_all(["div", "span"], string=re.compile(r"\d+\s*mm")):
            if isinstance(element, Tag):
                mm_match = re.search(r"(\d+)\s*mm", element.text)
                if mm_match:
                    result["precipitation"] = int(mm_match.group(1))
                    break

        return result


class HourlyForecastParser(WeatherParser):
    """Parser for hourly forecast data."""

    def parse(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Parse hourly forecast data."""
        result = {}
        forecast = []
        now = datetime.datetime.now(tz=datetime.UTC)
        current_hour = now.hour
        current_date = now.date()

        hourly_cards = soup.find_all("div", class_="ik new-hourly-forecast-card")

        last_hour = None
        days_offset = 0

        for card in hourly_cards:
            if not isinstance(card, Tag):
                continue

            forecast_item = self._parse_hourly_card(
                card, current_hour, current_date, days_offset
            )
            if forecast_item:
                forecast.append(forecast_item)
                # Track hour transitions to detect day changes
                hour_div = card.find("div", class_="ik new-hourly-forecast-hour")
                if hour_div and isinstance(hour_div, Tag):
                    hour = hour_div.text.strip()
                    hour_int = int(hour.split(":")[0])
                    if last_hour is not None and hour_int < last_hour:
                        days_offset += 1
                    last_hour = hour_int

        if forecast:
            # Sort by datetime to ensure chronological order
            forecast.sort(key=lambda x: x["datetime"])
            result["hourly_forecast"] = forecast

        return result

    def _parse_hourly_card(
        self,
        card: Tag,
        current_hour: int,
        current_date: datetime.date,
        days_offset: int,
    ) -> dict[str, Any] | None:
        """Parse individual hourly forecast card."""
        hour_div = card.find("div", class_="ik new-hourly-forecast-hour")
        temp_div = card.find("div", class_="ik tempValue")

        if not (
            hour_div
            and temp_div
            and isinstance(hour_div, Tag)
            and isinstance(temp_div, Tag)
        ):
            return None

        temp_a = temp_div.find("a")
        temp = None
        if temp_a and isinstance(temp_a, Tag):
            with contextlib.suppress(ValueError):
                temp = int(temp_a.text.strip())

        condition = self.extract_condition(card)
        precipitation, precipitation_probability = self.extract_precipitation_data(card)

        try:
            dt = self.extract_datetime(
                current_hour, current_date, hour_div, days_offset
            )

            return {
                "datetime": dt.isoformat(),
                "temperature": temp,
                "condition": condition,
                "precipitation": precipitation,
                "precipitation_probability": precipitation_probability,
            }
        except (ValueError, IndexError):
            return None

    def extract_datetime(
        self,
        current_hour: int,
        current_date: datetime.date,
        hour_div: Tag,
        days_offset: int,
    ) -> datetime.datetime:
        """Calculate the forecast datetime based on hour and date."""
        hour = hour_div.text.strip()
        hour_int = int(hour.split(":")[0])
        minute_int = int(hour.split(":")[1]) if ":" in hour else 0

        # Start with current date plus the days offset from tracking hour rollover
        forecast_date = current_date + datetime.timedelta(days=days_offset)

        # For the first day (days_offset==0), skip hours that have already passed
        if days_offset == 0 and hour_int < current_hour:
            forecast_date = current_date + datetime.timedelta(days=1)

        return datetime.datetime.combine(
            forecast_date, datetime.time(hour_int, minute_int)
        )

    def extract_condition(self, card: Tag) -> str | None:
        """Extract weather condition from the icon container tag."""
        icon_container_elem = card.find("div", class_="forecast-icon-container")
        icon_container = (
            icon_container_elem if isinstance(icon_container_elem, Tag) else None
        )
        condition = None
        if icon_container and isinstance(icon_container, Tag):
            icon_a = icon_container.find("a")
            if icon_a and isinstance(icon_a, Tag):
                condition_val = icon_a.get("data-bs-content")
                if isinstance(condition_val, str):
                    condition = WeatherConditionMapper.map_condition(condition_val)
        return condition

    def extract_precipitation_data(self, card: Tag) -> tuple[int, int]:
        """Extract precipitation data from hourly card."""
        precipitation_probability = self.extract_precipitation_probability(card)
        precipitation = self.extract_precipitation_amount(card)
        return precipitation, precipitation_probability

    def extract_precipitation_probability(self, card: Tag) -> int:
        """Extract precipitation probability."""
        rain_chance_div = card.find("div", class_="ik hourly-rain-chance")
        if not (rain_chance_div and isinstance(rain_chance_div, Tag)):
            return 0

        rain_a = rain_chance_div.find("a")
        if not (rain_a and isinstance(rain_a, Tag)):
            return 0

        rain_text = rain_a.text.strip()
        if not rain_text.endswith("%"):
            return 0

        try:
            return int(rain_text[:-1])
        except ValueError:
            return 0

    def extract_precipitation_amount(self, card: Tag) -> int:
        """Extract precipitation amount."""
        rainlevel_pattern = re.compile(r"ik rainlevel-\d+")
        rainlevel_divs = card.find_all("div", class_=rainlevel_pattern)

        for rainlevel_div in rainlevel_divs:
            if not isinstance(rainlevel_div, Tag):
                continue

            precipitation = self.parse_rainlevel_class(rainlevel_div)
            if precipitation > 0:
                return precipitation

        return 0

    def parse_rainlevel_class(self, rainlevel_div: Tag) -> int:
        """Parse rainlevel class."""
        class_attr = rainlevel_div.get("class")
        if not class_attr:
            return 0

        class_list = class_attr if isinstance(class_attr, list) else [class_attr]

        for class_name in class_list:
            if isinstance(class_name, str) and class_name.startswith("rainlevel-"):
                try:
                    precip_match = re.search(r"rainlevel-(\d+)", class_name)
                    if precip_match:
                        return int(precip_match.group(1))
                except ValueError:
                    continue

        return 0


class DailyForecastParser(WeatherParser):
    """Parser for daily forecast data."""

    def parse(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Parse daily forecast data."""
        result = {}
        daily_forecast = []
        daily_cols = soup.find_all("div", class_="ik dailyForecastCol")
        today = datetime.datetime.now(tz=datetime.UTC).date()

        for i, col in enumerate(daily_cols):
            if not isinstance(col, Tag):
                continue

            forecast_date = today + datetime.timedelta(days=i)
            forecast_item = self._parse_daily_column(col, forecast_date)
            daily_forecast.append(forecast_item)

        if daily_forecast:
            result["daily_forecast"] = daily_forecast

        return result

    def _parse_daily_column(
        self, col: Tag, forecast_date: datetime.date
    ) -> dict[str, Any]:
        """Parse individual daily forecast column."""
        min_temp, max_temp = self.extract_temperatures(col)
        condition = self.extract_condition(col)
        precipitation = self.extract_precipitation(col)
        precipitation_probability = self.extract_precipitation_probability(col)

        return {
            "datetime": str(forecast_date),
            "temperature": max_temp,
            "templow": min_temp,
            "condition": condition,
            "precipitation": precipitation,
            "precipitation_probability": precipitation_probability,
        }

    def extract_temperatures(self, col: Tag) -> tuple[int | None, int | None]:
        """
        Extract min and max temperatures from column.

        Returns:
            tuple: (min_temp, max_temp)

        """
        # First check for min-max-close or min-max-closer div (when temps are close)
        close_div = col.find("div", class_=["ik min-max-close", "ik min-max-closer"])
        if close_div and isinstance(close_div, Tag):
            a_tags = close_div.find_all("a")
            min_required_tags = 2
            if len(a_tags) >= min_required_tags:
                # First <a> is max, second is min
                max_match = re.search(r"(-?\d+)", a_tags[0].get_text(strip=True))
                min_match = re.search(r"(-?\d+)", a_tags[1].get_text(strip=True))
                max_temp = int(max_match.group(1)) if max_match else None
                min_temp = int(min_match.group(1)) if min_match else None
                return (min_temp, max_temp)

        # Otherwise, look for separate max and min divs
        min_temp = self.extract_temperature(col, "ik min")
        max_temp = self.extract_temperature(col, "ik max")
        return (min_temp, max_temp)

    def extract_temperature(self, col: Tag, class_name: str) -> int | None:
        """Extract temperature from column."""
        temp_div = col.find("div", class_=class_name)
        if temp_div and isinstance(temp_div, Tag):
            temp_a = temp_div.find("a")
            if temp_a and isinstance(temp_a, Tag):
                match = re.search(r"(-?\d+)", temp_a.get_text(strip=True))
                if match:
                    return int(match.group(1))
        return None

    def extract_condition(self, col: Tag) -> str | None:
        """Extract weather condition from column."""
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
            return WeatherConditionMapper.map_condition(match.group(1).strip())

        # Try simpler match as fallback
        text_match = re.search(r"popover-icon' src='[^']+'>([^<]+)", popover)
        if text_match:
            return WeatherConditionMapper.map_condition(text_match.group(1).strip())

        return None

    def extract_precipitation(self, col: Tag) -> int:
        """Extract precipitation amount."""
        precip_span = col.find("span", class_="ik mm")
        if precip_span and isinstance(precip_span, Tag):
            precip_text = precip_span.text.strip()
            if precip_text:
                match = re.search(r"(\d+)", precip_text)
                if match:
                    return int(match.group(1))
        return 0

    def extract_precipitation_probability(self, col: Tag) -> int:
        """Extract precipitation probability."""
        # Look for percentage values
        for element in col.find_all(["span", "div", "a"], string=re.compile(r"\d+%")):
            if isinstance(element, Tag):
                percent_text = element.text.strip()
                if percent_text.endswith("%"):
                    try:
                        return int(percent_text[:-1])
                    except ValueError:
                        continue

        # Look for data attributes
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


# Main API client - simplified and focused
class IdokepApiClient:
    """Refactored API client with separation of concerns."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._http_client = HttpClient(session)
        self._current_parser = CurrentWeatherParser()
        self._hourly_parser = HourlyForecastParser()
        self._daily_parser = DailyForecastParser()

    async def check_connectivity(self) -> bool:
        """Check if idokep.hu is reachable."""
        return await self._http_client.check_connectivity()

    async def async_get_weather_data(self, location: str) -> dict[str, Any]:
        """Get comprehensive weather data for location."""
        # Check connectivity first
        if not await self.check_connectivity():
            LOGGER.warning(
                "No internet connectivity to idokep.hu, skipping weather data update"
            )
            msg = "No internet connectivity to idokep.hu"
            raise IdokepApiClientConnectivityError(msg)

        urls = [
            IdokepConfig.get_current_weather_url(location),
            IdokepConfig.get_hourly_forecast_url(location),
            IdokepConfig.get_daily_forecast_url(location),
        ]

        try:
            # Use backward compatibility methods for test compatibility
            results = await asyncio.gather(
                self._scrape_current_weather(urls[0]),
                self._scrape_hourly_forecast(urls[1]),
                self._scrape_daily_forecast(urls[2]),
                return_exceptions=True,
            )

            # Combine results, handling both successful data and exceptions
            data = {}
            for result in results:
                if isinstance(result, dict):
                    data.update(result)
                elif isinstance(result, Exception):
                    LOGGER.warning("Failed to scrape some weather data: %s", result)
        except (aiohttp.ClientError, TimeoutError, socket.gaierror) as exc:
            LOGGER.error("Error scraping Idokep: %s", exc)
            return {}
        return data

    async def _scrape_and_parse(
        self, url: str, parser: WeatherParser
    ) -> dict[str, Any]:
        """Scrape URL and parse with given parser."""
        try:
            html = await self._http_client.get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            return parser.parse(soup)
        except (
            aiohttp.ClientError,
            TimeoutError,
            socket.gaierror,
            IdokepApiClientCommunicationError,
        ) as exc:
            LOGGER.error("Error scraping %s: %s", url, exc)
            return {}

    # Backward compatibility scrape methods for tests
    async def _scrape_current_weather(self, url: str) -> dict[str, Any]:
        """Scrape current weather data."""
        try:
            return await self._scrape_and_parse(url, self._current_parser)
        except (
            aiohttp.ClientError,
            TimeoutError,
            socket.gaierror,
            IdokepApiClientCommunicationError,
        ):
            return {}

    async def _scrape_hourly_forecast(self, url: str) -> dict[str, Any]:
        """Scrape hourly forecast data."""
        try:
            return await self._scrape_and_parse(url, self._hourly_parser)
        except (
            aiohttp.ClientError,
            TimeoutError,
            socket.gaierror,
            IdokepApiClientCommunicationError,
        ):
            return {}

    async def _scrape_daily_forecast(self, url: str) -> dict[str, Any]:
        """Scrape daily forecast data."""
        try:
            return await self._scrape_and_parse(url, self._daily_parser)
        except (
            aiohttp.ClientError,
            TimeoutError,
            socket.gaierror,
            IdokepApiClientCommunicationError,
        ):
            return {}

    @property
    def _session(self) -> aiohttp.ClientSession:
        """Backward compatibility property for accessing the session."""
        return self._http_client.session

    # Public API methods for backward compatibility
    def map_condition(self, condition: str) -> str:
        """Map Hungarian condition to Home Assistant standard condition."""
        return WeatherConditionMapper.map_condition(condition)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(IdokepConfig.TIMEOUT):
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

    # Parsing method compatibility wrappers
    def _parse_sunrise_sunset(self, soup: BeautifulSoup) -> dict:
        """Extract sunrise and sunset times."""
        return self._current_parser.parse_sunrise_sunset(soup)

    def _parse_short_forecast(self, soup: BeautifulSoup) -> str | None:
        """Extract short forecast text."""
        return self._current_parser.parse_short_forecast(soup)

    def _extract_current_precipitation(self, soup: BeautifulSoup) -> dict:
        """Extract current precipitation data."""
        return self._current_parser.extract_current_precipitation(soup)

    def _extract_hourly_precipitation_data(self, card: Tag) -> tuple[int, int]:
        """Extract precipitation data from hourly card."""
        return self._hourly_parser.extract_precipitation_data(card)

    def _extract_precipitation_probability(self, card: Tag) -> int:
        """Extract precipitation probability."""
        return self._hourly_parser.extract_precipitation_probability(card)

    def _extract_precipitation_amount(self, card: Tag) -> int:
        """Extract precipitation amount."""
        return self._hourly_parser.extract_precipitation_amount(card)

    def _parse_rainlevel_class(self, rainlevel_div: Tag) -> int:
        """Parse rainlevel class."""
        return self._hourly_parser.parse_rainlevel_class(rainlevel_div)

    def _extract_daily_temperature(self, col: Tag, class_name: str) -> int | None:
        """Extract temperature from daily forecast column."""
        return self._daily_parser.extract_temperature(col, class_name)

    def _extract_daily_condition(self, col: Tag) -> str | None:
        """Extract weather condition from daily forecast column."""
        return self._daily_parser.extract_condition(col)

    def _extract_daily_precipitation(self, col: Tag) -> int:
        """Extract precipitation from daily forecast column."""
        return self._daily_parser.extract_precipitation(col)

    def _extract_daily_precipitation_probability(self, col: Tag) -> int:
        """Extract precipitation probability from daily forecast column."""
        return self._daily_parser.extract_precipitation_probability(col)

    def _extract_time_from_text(
        self,
        label: str,
        _div: Tag,
        today: datetime.date,
        local_tz: datetime.tzinfo,
        text: str,
    ) -> str | None:
        """Extract time from text."""
        return TimeUtils.extract_time_from_text(label, text, today, local_tz)


# Compatibility function for tests
def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise IdokepApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


# Factory function for easy creation
def create_idokep_client(session: aiohttp.ClientSession) -> IdokepApiClient:
    """Create an IdokepApiClient instance."""
    return IdokepApiClient(session)
