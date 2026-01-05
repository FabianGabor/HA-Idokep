"""Unit tests for weather alert parsing."""

from __future__ import annotations

from bs4 import BeautifulSoup

from custom_components.idokep.api import AlertParser


class TestAlertParser:
    """Test alert parsing functionality."""

    def test_parse_general_alert_yellow(self) -> None:
        """Test parsing yellow general alert."""
        html = """
        <div class="container ik alert-bar yellow p-0" id="topalertbar">
            <a href="/radar#riasztas">
                <i class="fas fa-fw fa-exclamation-triangle"></i>
                Sárga riasztás ónos esőre
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 1
        alert = result["alerts"][0]
        assert alert.level == "yellow"
        assert alert.type == "freezing_rain"
        assert "ónos esőre" in alert.description

    def test_parse_general_alert_orange(self) -> None:
        """Test parsing orange general alert."""
        html = """
        <div class="container ik alert-bar orange p-0" id="topalertbar">
            <a href="/radar#riasztas">
                <i class="fas fa-fw fa-exclamation-triangle"></i>
                Narancs riasztás zivatar
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 1
        alert = result["alerts"][0]
        assert alert.level == "orange"
        assert alert.type == "thunderstorm"

    def test_parse_general_alert_red(self) -> None:
        """Test parsing red general alert."""
        html = """
        <div class="container ik alert-bar red p-0" id="topalertbar">
            <a href="/radar#riasztas">
                <i class="fas fa-fw fa-exclamation-triangle"></i> Piros riasztás vihar
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 1
        alert = result["alerts"][0]
        assert alert.level == "red"
        assert alert.type == "storm"

    def test_parse_hourly_alert(self) -> None:
        """Test parsing hourly forecast alert."""
        html = """
        <div class="ik genericHourlyAlert">
            <a tabindex="0" class="ik d-block w-100 hover-over"
               data-bs-toggle="popover" data-bs-placement="bottom"
               data-bs-content="Sárga riasztás ónos esőre"
               data-bs-original-title="" title="">
                <img class="ik forecast-alert-icon"
                     alt="Sárga riasztás ónos esőre"
                     src="/images/elore3/figyikonok2/onoseso.png"
                     width="40" height="40">
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 1
        alert = result["alerts"][0]
        assert alert.level == "yellow"
        assert alert.type == "freezing_rain"
        assert alert.icon_url is not None
        assert "onoseso.png" in alert.icon_url

    def test_parse_multiple_hourly_alerts(self) -> None:
        """Test parsing multiple different hourly alerts."""
        html = """
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Sárga riasztás szélre">
                <img class="ik forecast-alert-icon" src="/images/alerts/wind.png">
            </a>
        </div>
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Narancs riasztás zivatar">
                <img class="ik forecast-alert-icon" src="/images/alerts/thunder.png">
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 2
        assert result["alerts"][0].level == "yellow"
        assert result["alerts"][0].type == "wind"
        assert result["alerts"][1].level == "orange"
        assert result["alerts"][1].type == "thunderstorm"

    def test_alerts_organized_by_level(self) -> None:
        """Test that alerts are properly organized by severity level."""
        html = """
        <div class="container ik alert-bar yellow p-0" id="topalertbar">
            <a href="/radar#riasztas">Sárga riasztás szélre</a>
        </div>
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Narancs riasztás zivatar">
                <img class="ik forecast-alert-icon" src="/images/alerts/thunder.png">
            </a>
        </div>
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Piros riasztás vihar">
                <img class="ik forecast-alert-icon" src="/images/alerts/storm.png">
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts_by_level" in result
        by_level = result["alerts_by_level"]

        assert len(by_level["yellow"]) == 1
        assert len(by_level["orange"]) == 1
        assert len(by_level["red"]) == 1

        assert by_level["yellow"][0]["type"] == "wind"
        assert by_level["orange"][0]["type"] == "thunderstorm"
        assert by_level["red"][0]["type"] == "storm"

    def test_no_alerts(self) -> None:
        """Test parsing when no alerts are present."""
        html = """
        <div class="some-other-content">
            <p>No alerts today</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert "alerts" in result
        assert len(result["alerts"]) == 0
        assert "alerts_by_level" in result
        assert len(result["alerts_by_level"]["yellow"]) == 0
        assert len(result["alerts_by_level"]["orange"]) == 0
        assert len(result["alerts_by_level"]["red"]) == 0

    def test_alert_type_extraction_heat(self) -> None:
        """Test alert type extraction for heat warning."""
        html = """
        <div class="container ik alert-bar orange p-0" id="topalertbar">
            <a href="/radar#riasztas">Narancs riasztás hőségre</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert result["alerts"][0].type == "heat"

    def test_alert_type_extraction_fog(self) -> None:
        """Test alert type extraction for fog warning."""
        html = """
        <div class="container ik alert-bar yellow p-0" id="topalertbar">
            <a href="/radar#riasztas">Sárga riasztás ködre</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        assert result["alerts"][0].type == "fog"

    def test_duplicate_alerts_removed(self) -> None:
        """Test that duplicate alerts are not added multiple times."""
        html = """
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Sárga riasztás szélre">
                <img class="ik forecast-alert-icon" src="/images/alerts/wind.png">
            </a>
        </div>
        <div class="ik genericHourlyAlert">
            <a class="ik d-block w-100 hover-over"
               data-bs-content="Sárga riasztás szélre">
                <img class="ik forecast-alert-icon" src="/images/alerts/wind.png">
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        parser = AlertParser()
        result = parser.parse(soup)

        # Should only have 1 alert, not 2
        assert len(result["alerts"]) == 1
