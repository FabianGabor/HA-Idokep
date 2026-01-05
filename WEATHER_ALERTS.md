# Weather Alerts Implementation

## Overview

This integration now supports Időkép weather alerts with comprehensive binary sensors that provide both alert presence detection and detailed alert information through attributes.

## Binary Sensors

The integration creates the following binary sensors for weather alerts:

### 1. Main Weather Alert Sensor (`binary_sensor.weather_alert`)

**Purpose**: Indicates if ANY weather alert is currently active

**State**:
- `on` - At least one alert is active
- `off` - No alerts active

**Attributes**:
```yaml
alert_count: 2              # Total number of active alerts
yellow_alerts: 1            # Number of yellow alerts
orange_alerts: 1            # Number of orange alerts
red_alerts: 0               # Number of red alerts
alerts:                     # List of all alerts with details
  - level: "yellow"
    type: "wind"
    description: "Sárga riasztás szélre"
    icon_url: "https://www.idokep.hu/images/..."
  - level: "orange"
    type: "thunderstorm"
    description: "Narancs riasztás zivatar"
    icon_url: "https://www.idokep.hu/images/..."
```

### 2. Yellow Alert Sensor (`binary_sensor.alert_yellow`)

**Purpose**: Indicates if any YELLOW (sárga) alerts are active

**State**:
- `on` - At least one yellow alert active
- `off` - No yellow alerts

**Attributes**:
```yaml
alert_count: 2              # Number of yellow alerts
alerts:                     # List of yellow alerts
  - type: "wind"
    description: "Sárga riasztás szélre"
    icon_url: "https://www.idokep.hu/images/..."
  - type: "freezing_rain"
    description: "Sárga riasztás ónos esőre"
    icon_url: "https://www.idokep.hu/images/..."
```

### 3. Orange Alert Sensor (`binary_sensor.alert_orange`)

**Purpose**: Indicates if any ORANGE (narancs) alerts are active

**State**:
- `on` - At least one orange alert active
- `off` - No orange alerts

**Attributes**:
```yaml
alert_count: 1              # Number of orange alerts
alerts:                     # List of orange alerts
  - type: "thunderstorm"
    description: "Narancs riasztás zivatar"
    icon_url: "https://www.idokep.hu/images/..."
```

### 4. Red Alert Sensor (`binary_sensor.alert_red`)

**Purpose**: Indicates if any RED (piros/vörös) alerts are active

**State**:
- `on` - At least one red alert active
- `off` - No red alerts

**Attributes**:
```yaml
alert_count: 1              # Number of red alerts
alerts:                     # List of red alerts
  - type: "storm"
    description: "Piros riasztás vihar"
    icon_url: "https://www.idokep.hu/images/..."
```

## Alert Types

The integration recognizes and standardizes the following alert types:

| Hungarian Term | English Type | Description |
|---------------|--------------|-------------|
| ónos eső | freezing_rain | Freezing rain warning |
| vihar | storm | Storm warning |
| zivatar | thunderstorm | Thunderstorm warning |
| szél | wind | Wind warning |
| hó | snow | Snow warning |
| eső | rain | Rain warning |
| köd | fog | Fog warning |
| hőség | heat | Heat warning |
| hideg | cold | Cold warning |
| fagy | frost | Frost warning |

## Data Sources

The integration parses alerts from two locations on the Időkép website:

### 1. General Alert Bar (Top of Page)
```html
<div class="container ik alert-bar yellow p-0" id="topalertbar">
    <a href="/radar#riasztas">
        <i class="fas fa-fw fa-exclamation-triangle"></i>
        Sárga riasztás ónos esőre
    </a>
</div>
```

### 2. Hourly Forecast Alerts
```html
<div class="ik genericHourlyAlert">
    <a class="ik d-block w-100 hover-over"
       data-bs-content="Sárga riasztás ónos esőre">
        <img class="ik forecast-alert-icon"
             src="/images/elore3/figyikonok2/onoseso.png">
    </a>
</div>
```

## Automation Examples

### Example 1: Notify on Any Alert
```yaml
automation:
  - alias: "Weather Alert Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.weather_alert
        to: 'on'
    action:
      - service: notify.mobile_app
        data:
          title: "Weather Alert!"
          message: >
            {{ state_attr('binary_sensor.weather_alert', 'alert_count') }}
            alert(s) active
```

### Example 2: Critical Red Alert
```yaml
automation:
  - alias: "Critical Weather Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.alert_red
        to: 'on'
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 CRITICAL WEATHER ALERT"
          message: >
            {% for alert in state_attr('binary_sensor.alert_red', 'alerts') %}
            {{ alert.description }}
            {% endfor %}
          data:
            priority: high
            sound: alarm.mp3
```

### Example 3: Multiple Alert Types
```yaml
automation:
  - alias: "Wind and Thunder Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.alert_yellow
        to: 'on'
      - platform: state
        entity_id: binary_sensor.alert_orange
        to: 'on'
    condition:
      - condition: template
        value_template: >
          {% set yellow = state_attr('binary_sensor.alert_yellow', 'alerts') or [] %}
          {% set orange = state_attr('binary_sensor.alert_orange', 'alerts') or [] %}
          {% set all_alerts = yellow + orange %}
          {{ all_alerts | selectattr('type', 'eq', 'wind') | list | length > 0
             and all_alerts | selectattr('type', 'eq', 'thunderstorm') | list | length > 0 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Warning: Both wind and thunderstorm alerts active!"
```

### Example 4: Dashboard Card
```yaml
type: entities
title: Weather Alerts
entities:
  - entity: binary_sensor.weather_alert
    name: Any Active Alerts
  - type: attribute
    entity: binary_sensor.weather_alert
    attribute: alert_count
    name: Total Alerts
  - entity: binary_sensor.alert_yellow
    name: Yellow Alerts
  - entity: binary_sensor.alert_orange
    name: Orange Alerts
  - entity: binary_sensor.alert_red
    name: Red Alerts
```

## Technical Implementation

### API Client (`api.py`)
- New `AlertData` dataclass for structured alert data
- New `AlertParser` class that inherits from `WeatherParser`
- Parses both general and hourly alerts
- Deduplicates alerts automatically
- Organizes alerts by severity level
- Extracts alert type, description, and icon URL

### Binary Sensor (`binary_sensor.py`)
- Four new binary sensor entities
- Attributes dynamically populated from coordinator data
- Efficient checking methods for each alert level
- Dictionary-based sensor logic to avoid code duplication

### Translations
- English and Hungarian translations provided
- Proper naming for all sensor entities
- Device class set to `SAFETY` for alert sensors

## Testing

Comprehensive test suite in `tests/test_alerts.py`:
- General alert parsing (yellow, orange, red)
- Hourly alert parsing
- Multiple simultaneous alerts
- Alert organization by level
- Alert type extraction
- Duplicate detection
- No alerts scenario

All 10 tests pass successfully.

## Future Enhancements

Possible future improvements:
1. Alert expiry time tracking
2. Alert history
3. Push notification integration
4. Alert severity comparison
5. Geographic area affected by alert
6. Alert effective time periods
