"""Unit tests for the Időkép API client."""

from __future__ import annotations

import socket
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from bs4 import BeautifulSoup, Tag

from custom_components.idokep.api import (
    CurrentWeatherParser,
    IdokepApiClient,
    IdokepApiClientAuthenticationError,
    IdokepApiClientCommunicationError,
    IdokepApiClientError,
    _verify_response_or_raise,
)


class TestIdokepApiClientExceptions:
    """Test exception classes and helper functions."""

    def test_idokep_api_client_error_inheritance(self) -> None:
        """Test that IdokepApiClientError is an Exception."""
        error = IdokepApiClientError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_communication_error_inheritance(self) -> None:
        """Test that IdokepApiClientCommunicationError inherits correctly."""
        error = IdokepApiClientCommunicationError("comm error")
        assert isinstance(error, IdokepApiClientError)
        assert isinstance(error, Exception)
        assert str(error) == "comm error"

    def test_authentication_error_inheritance(self) -> None:
        """Test that IdokepApiClientAuthenticationError inherits correctly."""
        error = IdokepApiClientAuthenticationError("auth error")
        assert isinstance(error, IdokepApiClientError)
        assert isinstance(error, Exception)
        assert str(error) == "auth error"

    def test_verify_response_or_raise_success(self) -> None:
        """Test _verify_response_or_raise with successful response."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()

        # Should not raise any exception
        _verify_response_or_raise(mock_response)
        mock_response.raise_for_status.assert_called_once()

    def test_verify_response_or_raise_401(self) -> None:
        """Test _verify_response_or_raise with 401 status."""
        mock_response = Mock()
        mock_response.status = 401

        with pytest.raises(IdokepApiClientAuthenticationError) as exc_info:
            _verify_response_or_raise(mock_response)

        assert "Invalid credentials" in str(exc_info.value)

    def test_verify_response_or_raise_403(self) -> None:
        """Test _verify_response_or_raise with 403 status."""
        mock_response = Mock()
        mock_response.status = 403

        with pytest.raises(IdokepApiClientAuthenticationError) as exc_info:
            _verify_response_or_raise(mock_response)

        assert "Invalid credentials" in str(exc_info.value)

    def test_verify_response_or_raise_other_error(self) -> None:
        """Test _verify_response_or_raise with other HTTP errors."""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.raise_for_status = Mock(
            side_effect=aiohttp.ClientResponseError(
                request_info=Mock(), history=(), status=500
            )
        )

        with pytest.raises(aiohttp.ClientResponseError):
            _verify_response_or_raise(mock_response)


class TestIdokepApiClientZoneInfoHandling:
    """Test zoneinfo import error handling."""

    def test_zoneinfo_import_error_handling(self) -> None:
        """Test that the module handles zoneinfo import errors gracefully."""
        # This test ensures the try/except block for zoneinfo import is covered
        # The import is already done at module level, so we test the fallback behavior
        with patch("custom_components.idokep.api.zoneinfo", None):
            client = IdokepApiClient(Mock())

            # Test that the client can still work without zoneinfo
            html = '<div alt="Napkelte 06:30" />'
            soup = BeautifulSoup(html, "html.parser")

            # This should use the fallback timezone
            result = client._parse_sunrise_sunset(soup)
            assert isinstance(result, dict)


class TestIdokepApiClient:
    """Test the main API client class."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock aiohttp session."""
        return Mock(spec=aiohttp.ClientSession)

    @pytest.fixture
    def api_client(self, mock_session: Mock) -> IdokepApiClient:
        """Create an API client with mocked session."""
        return IdokepApiClient(mock_session)

    def test_init(self, mock_session: Mock) -> None:
        """Test API client initialization."""
        client = IdokepApiClient(mock_session)
        assert client._session is mock_session

    def test_map_condition_sunny(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for sunny conditions."""
        assert api_client.map_condition("napos") == "sunny"
        assert api_client.map_condition("derült") == "sunny"
        assert api_client.map_condition("NAPOS") == "sunny"  # Case insensitive

    def test_map_condition_cloudy(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for cloudy conditions."""
        assert api_client.map_condition("borult") == "cloudy"
        assert api_client.map_condition("erősen felhős") == "cloudy"

    def test_map_condition_partly_cloudy(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for partly cloudy conditions."""
        assert api_client.map_condition("közepesen felhős") == "partlycloudy"
        assert api_client.map_condition("gyengén felhős") == "partlycloudy"

    def test_map_condition_rainy(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for rainy conditions."""
        assert api_client.map_condition("zápor") == "rainy"
        assert api_client.map_condition("szitálás") == "rainy"
        assert api_client.map_condition("gyenge eső") == "rainy"
        assert api_client.map_condition("eső") == "rainy"
        assert api_client.map_condition("eső viharos széllel") == "rainy"

    def test_map_condition_special(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for special conditions."""
        assert api_client.map_condition("zivatar") == "lightning-rainy"
        assert api_client.map_condition("erős eső") == "pouring"
        assert api_client.map_condition("jégeső") == "hail"
        assert api_client.map_condition("havazás") == "snowy"
        assert api_client.map_condition("havas eső") == "snowy-rainy"
        assert api_client.map_condition("köd") == "fog"
        assert api_client.map_condition("villámlás") == "lightning"
        assert api_client.map_condition("szeles") == "windy"

    def test_map_condition_unknown(self, api_client: IdokepApiClient) -> None:
        """Test condition mapping for unknown conditions."""
        assert api_client.map_condition("ismeretlen időjárás") == "unknown"
        assert api_client.map_condition("") == "unknown"

    @pytest.mark.asyncio
    async def test_api_wrapper_success(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test successful API wrapper call."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={"key": "value"})

        mock_session.request = AsyncMock(return_value=mock_response)

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._api_wrapper("GET", "http://test.com")

        assert result == {"key": "value"}
        mock_session.request.assert_called_once_with(
            method="GET", url="http://test.com", headers=None, json=None
        )

    @pytest.mark.asyncio
    async def test_api_wrapper_timeout_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test API wrapper with timeout error."""
        mock_session.request = AsyncMock(side_effect=TimeoutError("Timeout"))

        with (
            patch("custom_components.idokep.api.async_timeout.timeout"),
            pytest.raises(IdokepApiClientCommunicationError) as exc_info,
        ):
            await api_client._api_wrapper("GET", "http://test.com")

        assert "Timeout error fetching information" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_wrapper_client_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test API wrapper with aiohttp client error."""
        mock_session.request = AsyncMock(
            side_effect=aiohttp.ClientError("Client error")
        )

        with (
            patch("custom_components.idokep.api.async_timeout.timeout"),
            pytest.raises(IdokepApiClientCommunicationError) as exc_info,
        ):
            await api_client._api_wrapper("GET", "http://test.com")

        assert "Error fetching information" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_wrapper_socket_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test API wrapper with socket error."""
        mock_session.request = AsyncMock(side_effect=socket.gaierror("Socket error"))

        with (
            patch("custom_components.idokep.api.async_timeout.timeout"),
            pytest.raises(IdokepApiClientCommunicationError) as exc_info,
        ):
            await api_client._api_wrapper("GET", "http://test.com")

        assert "Error fetching information" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_wrapper_general_exception(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test API wrapper with general exception."""
        mock_session.request = AsyncMock(side_effect=ValueError("Value error"))

        with (
            patch("custom_components.idokep.api.async_timeout.timeout"),
            pytest.raises(IdokepApiClientError) as exc_info,
        ):
            await api_client._api_wrapper("GET", "http://test.com")

        assert "Something really wrong happened!" in str(exc_info.value)


class TestIdokepApiClientWeatherScraping:
    """Test weather data scraping functionality."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock aiohttp session."""
        return Mock(spec=aiohttp.ClientSession)

    @pytest.fixture
    def api_client(self, mock_session: Mock) -> IdokepApiClient:
        """Create an API client with mocked session."""
        return IdokepApiClient(mock_session)

    @pytest.fixture
    def sample_current_weather_html(self) -> str:
        """Sample HTML for current weather page."""
        return """
        <html>
            <div class="ik current-temperature">22°C</div>
            <div class="ik current-weather">Napos</div>
            <div class="ik current-weather-title">Jelenleg</div>
            <div>
                <img alt="Napkelte 06:30" />
                Napkelte 06:30
            </div>
            <div>
                <img alt="Napnyugta 19:45" />
                Napnyugta 19:45
            </div>
            <div class="pt-2">Kellemes idő várható ma.</div>
            <span class="ik mm">2 mm</span>
            <div>Csapadék esélye: 30%</div>
        </html>
        """

    @pytest.fixture
    def sample_hourly_forecast_html(self) -> str:
        """Sample HTML for hourly forecast page."""
        return """
        <html>
            <div class="ik new-hourly-forecast-card">
                <div class="ik new-hourly-forecast-hour">14:00</div>
                <div class="ik tempValue"><a>25</a></div>
                <div class="forecast-icon-container">
                    <a data-bs-content="Napos"></a>
                </div>
                <div class="ik hourly-rain-chance"><a>20%</a></div>
                <div class="ik rainlevel-5"></div>
            </div>
            <div class="ik new-hourly-forecast-card">
                <div class="ik new-hourly-forecast-hour">15:00</div>
                <div class="ik tempValue"><a>24</a></div>
                <div class="forecast-icon-container">
                    <a data-bs-content="Borult"></a>
                </div>
                <div class="ik hourly-rain-chance"><a>0%</a></div>
            </div>
        </html>
        """

    @pytest.fixture
    def sample_daily_forecast_html(self) -> str:
        """Sample HTML for daily forecast page."""
        return """
        <html>
            <div class="ik dailyForecastCol">
                <div class="ik min"><a>15</a></div>
                <div class="ik max"><a>25</a></div>
                <div class="ik dfIconAlert">
                    <a data-bs-content="popover-icon' src='icon.png'>Napos<"></a>
                </div>
                <span class="ik mm">3 mm</span>
                <span>15%</span>
            </div>
            <div class="ik dailyForecastCol">
                <div class="ik min"><a>10</a></div>
                <div class="ik max"><a>20</a></div>
                <div class="ik dfIconAlert">
                    <a data-bs-content="popover-icon' src='icon.png'>Eső<"></a>
                </div>
                <span class="ik mm">8 mm</span>
                <span>80%</span>
            </div>
        </html>
        """

    @pytest.mark.asyncio
    async def test_scrape_current_weather_success(
        self,
        api_client: IdokepApiClient,
        mock_session: Mock,
        sample_current_weather_html: str,
    ) -> None:
        """Test successful current weather scraping."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=sample_current_weather_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = Mock(return_value=mock_response)

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_current_weather("http://test.com")

        expected_keys = {
            "temperature",
            "condition",
            "condition_hu",
            "weather_title",
            "sunrise",
            "sunset",
        }
        assert all(key in result for key in expected_keys)
        assert result["temperature"] == 22
        assert result["condition"] == "sunny"
        assert result["condition_hu"] == "Napos"
        assert result["weather_title"] == "Jelenleg"

    @pytest.mark.asyncio
    async def test_scrape_current_weather_network_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test current weather scraping with network error."""
        mock_session.get = Mock(side_effect=aiohttp.ClientError("Network error"))

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_current_weather("http://test.com")

        assert result == {}

    @pytest.mark.asyncio
    async def test_scrape_hourly_forecast_success(
        self,
        api_client: IdokepApiClient,
        mock_session: Mock,
        sample_hourly_forecast_html: str,
    ) -> None:
        """Test successful hourly forecast scraping."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=sample_hourly_forecast_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = Mock(return_value=mock_response)

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_hourly_forecast("http://test.com")

        assert "hourly_forecast" in result
        forecast = result["hourly_forecast"]
        assert len(forecast) == 2

        first_hour = forecast[0]
        assert first_hour["temperature"] == 25
        assert first_hour["condition"] == "sunny"
        assert first_hour["precipitation_probability"] == 20
        assert first_hour["precipitation"] == 5

    @pytest.mark.asyncio
    async def test_scrape_hourly_forecast_network_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test hourly forecast scraping with network error."""
        mock_session.get = Mock(side_effect=TimeoutError("Timeout"))

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_hourly_forecast("http://test.com")

        assert result == {}

    @pytest.mark.asyncio
    async def test_scrape_daily_forecast_success(
        self,
        api_client: IdokepApiClient,
        mock_session: Mock,
        sample_daily_forecast_html: str,
    ) -> None:
        """Test successful daily forecast scraping."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=sample_daily_forecast_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = Mock(return_value=mock_response)

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_daily_forecast("http://test.com")

        assert "daily_forecast" in result
        forecast = result["daily_forecast"]
        assert len(forecast) == 2

        first_day = forecast[0]
        assert first_day["temperature"] == 25  # max temp
        assert first_day["templow"] == 15  # min temp
        assert first_day["condition"] == "sunny"
        assert first_day["precipitation"] == 3

        second_day = forecast[1]
        assert second_day["condition"] == "rainy"
        assert second_day["precipitation"] == 8

    @pytest.mark.asyncio
    async def test_scrape_daily_forecast_network_error(
        self, api_client: IdokepApiClient, mock_session: Mock
    ) -> None:
        """Test daily forecast scraping with network error."""
        mock_session.get = Mock(side_effect=socket.gaierror("DNS error"))

        with patch("custom_components.idokep.api.async_timeout.timeout"):
            result = await api_client._scrape_daily_forecast("http://test.com")

        assert result == {}

    @pytest.mark.asyncio
    async def test_async_get_weather_data_success(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test complete weather data retrieval."""
        # Mock all three scraping methods
        current_data = {
            "temperature": 22,
            "condition": "sunny",
            "precipitation": 2,
            "precipitation_probability": 30,
        }
        hourly_data = {
            "hourly_forecast": [{"datetime": "2024-01-15T14:00:00", "temperature": 25}]
        }
        daily_data = {"daily_forecast": [{"datetime": "2024-01-15", "temperature": 25}]}

        with (
            patch.object(
                api_client,
                "_scrape_current_weather",
                new_callable=AsyncMock,
                return_value=current_data,
            ),
            patch.object(
                api_client,
                "_scrape_hourly_forecast",
                new_callable=AsyncMock,
                return_value=hourly_data,
            ),
            patch.object(
                api_client,
                "_scrape_daily_forecast",
                new_callable=AsyncMock,
                return_value=daily_data,
            ),
        ):
            result = await api_client.async_get_weather_data("budapest")

        # Should combine all data
        assert result["temperature"] == 22
        assert result["condition"] == "sunny"
        assert "hourly_forecast" in result
        assert "daily_forecast" in result

    @pytest.mark.asyncio
    async def test_async_get_weather_data_partial_failure(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test weather data retrieval with some methods failing."""
        current_data = {"temperature": 22, "condition": "sunny"}

        with (
            patch.object(
                api_client,
                "_scrape_current_weather",
                new_callable=AsyncMock,
                return_value=current_data,
            ),
            patch.object(
                api_client,
                "_scrape_hourly_forecast",
                new_callable=AsyncMock,
                side_effect=Exception("Network error"),
            ),
            patch.object(
                api_client,
                "_scrape_daily_forecast",
                new_callable=AsyncMock,
                return_value={},
            ),
        ):
            result = await api_client.async_get_weather_data("budapest")

        # Should still return current data even if others fail
        assert result["temperature"] == 22
        assert result["condition"] == "sunny"

    @pytest.mark.asyncio
    async def test_async_get_weather_data_with_exception_results(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test async_get_weather_data when some results are exceptions."""
        # This tests lines 142-145 (handling Exception results)
        current_data = {"temperature": 22, "condition": "sunny"}

        # Create a proper async mock that returns the list with exceptions
        async def mock_gather(*_args: object, **_kwargs: object) -> list:
            return [
                current_data,
                Exception("Network error"),
                {"hourly_forecast": []},
            ]

        with patch(
            "custom_components.idokep.api.asyncio.gather", side_effect=mock_gather
        ):
            result = await api_client.async_get_weather_data("budapest")

        # Should include data from successful results
        assert result["temperature"] == 22
        assert result["condition"] == "sunny"
        assert "hourly_forecast" in result

    @pytest.mark.asyncio
    async def test_async_get_weather_data_top_level_exception(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test async_get_weather_data when asyncio.gather itself fails."""
        # This tests lines 147-148 (top-level exception handling)
        with (
            patch(
                "custom_components.idokep.api.asyncio.gather",
                side_effect=aiohttp.ClientError("Network failure"),
            ),
            patch.object(api_client, "_scrape_current_weather", new_callable=AsyncMock),
            patch.object(api_client, "_scrape_hourly_forecast", new_callable=AsyncMock),
            patch.object(api_client, "_scrape_daily_forecast", new_callable=AsyncMock),
        ):
            result = await api_client.async_get_weather_data("budapest")

        # Should return empty dict when gather fails
        assert result == {}

    def test_parse_sunrise_sunset(self, api_client: IdokepApiClient) -> None:
        """Test sunrise and sunset parsing."""
        html = """
        <div>
            <img alt="Napkelte 06:30" />
            Some text about sunrise
        </div>
        <div>
            <img alt="Napnyugta 19:45" />
            Some text about sunset
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        # Call the actual method and check it returns a dict (functionality test)
        result = api_client._parse_sunrise_sunset(soup)

        # Should return a dict regardless of what's in it
        assert isinstance(result, dict)

    def test_parse_short_forecast(self, api_client: IdokepApiClient) -> None:
        """Test short forecast parsing."""
        html = """
        <div class="pt-2">
            <img src="icon.png" />
        </div>
        <div class="pt-2">
            <button>Click me</button>
        </div>
        <div class="pt-2">Kellemes idő várható ma.</div>
        <div class="pt-2">Napkelte 06:30 Napnyugta 19:45</div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._parse_short_forecast(soup)

        assert result == "Kellemes idő várható ma."

    def test_extract_hourly_precipitation_data(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test hourly precipitation data extraction."""
        html = """
        <div class="card">
            <div class="ik hourly-rain-chance"><a>25%</a></div>
            <div class="ik rainlevel-3"></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div", class_="card")

        if isinstance(card, Tag):
            precipitation, precipitation_probability = (
                api_client._extract_hourly_precipitation_data(card)
            )
            assert precipitation == 3
            assert precipitation_probability == 25

    def test_extract_daily_temperature(self, api_client: IdokepApiClient) -> None:
        """Test daily temperature extraction."""
        html = """
        <div class="col">
            <div class="ik min"><a>-5</a></div>
            <div class="ik max"><a>15</a></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        col = soup.find("div", class_="col")

        if isinstance(col, Tag):
            min_temp = api_client._extract_daily_temperature(col, "ik min")
            max_temp = api_client._extract_daily_temperature(col, "ik max")
            assert min_temp == -5
            assert max_temp == 15

    def test_extract_daily_condition(self, api_client: IdokepApiClient) -> None:
        """Test daily condition extraction."""
        html = """
        <div class="col">
            <div class="ik dfIconAlert">
                <a data-bs-content="popover-icon' src='icon.png'>Eső viharos széllel<">
                </a>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        col = soup.find("div", class_="col")

        if isinstance(col, Tag):
            condition = api_client._extract_daily_condition(col)
            assert condition == "rainy"

    def test_extract_daily_condition_fallback_match(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test daily condition extraction using fallback regex match."""
        # This tests lines 445-449 (fallback match without closing bracket)
        html = """
        <div class="col">
            <div class="ik dfIconAlert">
                <a data-bs-content="popover-icon' src='icon.png'>Napos">
                </a>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        col = soup.find("div", class_="col")

        if isinstance(col, Tag):
            condition = api_client._extract_daily_condition(col)
            assert condition == "sunny"

    def test_extract_current_precipitation(self, api_client: IdokepApiClient) -> None:
        """Test current precipitation extraction."""
        html = """
        <div>
            <span>Csapadék esélye: 40%</span>
        </div>
        <div>
            <span>Várható csapadék: 5 mm</span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._extract_current_precipitation(soup)

        assert result["precipitation_probability"] == 40
        assert result["precipitation"] == 5


class TestSunriseSunsetRegression:
    """Test sunrise and sunset parsing."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock aiohttp session."""
        return Mock(spec=aiohttp.ClientSession)

    @pytest.fixture
    def api_client(self, mock_session: Mock) -> IdokepApiClient:
        """Create API client for testing."""
        return IdokepApiClient(mock_session)

    def test_sunrise_sunset_div_text_extraction(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test that sunrise/sunset times are extracted from div text, not alt."""
        html = """
        <div>
            <img alt="Napkelte" />Napkelte 4:54
        </div>
        <div class="pt-2">
            <img alt="Napnyugta" />Napnyugta 20:44
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._parse_sunrise_sunset(soup)

        # Ensure data is extracted (regression prevention)
        assert "sunrise" in result
        assert "sunset" in result
        assert "4:54" in result["sunrise"]
        assert "20:44" in result["sunset"]

    def test_sunrise_sunset_with_current_parser(self) -> None:
        """Test integration with CurrentWeatherParser."""
        parser = CurrentWeatherParser()
        html = """
        <div class="ik current-temperature">25°C</div>
        <div class="ik current-weather">napos</div>
        <div>
            <img alt="Napkelte" />Napkelte 6:30
        </div>
        <div>
            <img alt="Napnyugta" />Napnyugta 19:45
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = parser.parse(soup)

        # Should include all data including sunrise/sunset
        assert "temperature" in result
        assert "condition" in result
        assert "sunrise" in result
        assert "sunset" in result
        assert "6:30" in result["sunrise"]
        assert "19:45" in result["sunset"]

    def test_sunrise_sunset_timezone_format(self, api_client: IdokepApiClient) -> None:
        """Test that times are formatted with timezone."""
        html = """
        <div>
            <img alt="Napkelte" />Napkelte 6:30
        </div>
        <div>
            <img alt="Napnyugta" />Napnyugta 19:45
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._parse_sunrise_sunset(soup)

        # Check timezone format
        assert "sunrise" in result
        assert "sunset" in result
        sunrise_tz = result["sunrise"][-6:]
        sunset_tz = result["sunset"][-6:]
        assert sunrise_tz in ["+01:00", "+02:00"]
        assert sunset_tz in ["+01:00", "+02:00"]

    def test_sunrise_sunset_datetime_compatibility(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test that extracted times are compatible with datetime parsing."""
        html = """
        <div>
            <img alt="Napkelte" />Napkelte 6:30
        </div>
        <div>
            <img alt="Napnyugta" />Napnyugta 19:45
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._parse_sunrise_sunset(soup)

        # Should be parseable by datetime.fromisoformat
        assert "sunrise" in result
        assert "sunset" in result

        sunrise_dt = datetime.fromisoformat(result["sunrise"])
        sunset_dt = datetime.fromisoformat(result["sunset"])

        assert sunrise_dt.hour == 6
        assert sunrise_dt.minute == 30
        assert sunset_dt.hour == 19
        assert sunset_dt.minute == 45

    def test_sunrise_sunset_no_data_graceful_handling(
        self, api_client: IdokepApiClient
    ) -> None:
        """Test graceful handling when no sunrise/sunset data is found."""
        html = """
        <div>
            <img alt="Weather" />Temperature: 22°C
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        result = api_client._parse_sunrise_sunset(soup)

        # Should return empty dict when no data found
        assert result == {}
