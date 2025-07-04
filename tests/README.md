# Test Documentation for Időkép Integration

This directory contains comprehensive unit tests for the Időkép Home Assistant integration.

## Test Structure

### Files

- `conftest.py` - Contains pytest fixtures and shared test configuration
- `test_weather.py` - Unit tests for the weather entity (`IdokepWeatherEntity`)
- `test_coordinator.py` - Unit tests for the data coordinator (`IdokepDataUpdateCoordinator`)

### Fixtures

The test suite uses the following fixtures defined in `conftest.py`:

- `mock_config_entry` - Mock configuration entry
- `mock_config_entry_data` - Mock configuration data
- `mock_hass` - Mock Home Assistant instance
- `mock_coordinator_data` - Mock weather data from coordinator
- `mock_coordinator` - Mock data update coordinator
- `mock_idokep_data` - Mock IdokepData
- `mock_api_client` - Mock API client

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Basic Test Run

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_weather.py -v

# Run specific test
pytest tests/test_weather.py::TestIdokepWeatherEntity::test_init_with_valid_location -v
```

### Test Coverage

```bash
# Run tests with coverage report
pytest tests/ --cov=custom_components.idokep --cov-report=html

# Run tests with coverage report in terminal
pytest tests/ --cov=custom_components.idokep --cov-report=term-missing
```

## Test Coverage

### Weather Entity Tests (`test_weather.py`)

The `IdokepWeatherEntity` class is thoroughly tested with the following scenarios:

#### Initialization Tests
- Valid location handling
- Special characters in location names
- Empty location fallback
- Location with only special characters
- Multiple consecutive underscores removal

#### Property Tests
- `device_info` property
- `has_entity_name` property
- `temperature` property (with and without data)
- `condition` property (with and without data)
- `native_temperature` property (including string conversion)
- `native_temperature_unit` property
- `supported_forecast_types` property
- `extra_state_attributes` property (with defaults)

#### Forecast Tests
- Hourly forecast retrieval
- Daily forecast retrieval
- Empty forecast handling

#### Device Integration Tests
- Device info initialization
- Device info with special location names

#### Setup Tests
- Entity setup entry point

### Coordinator Tests (`test_coordinator.py`)

The `IdokepDataUpdateCoordinator` class tests cover:

#### Error Handling Tests
- `NoWeatherDataError` initialization and message
- Data update with no weather data error
- Data update with general exceptions

#### Core Functionality Tests
- Coordinator initialization
- Successful data updates

## Test Patterns

### Mocking Strategy

Tests use `unittest.mock.Mock` and `AsyncMock` to isolate units under test:

- External dependencies are mocked (Home Assistant core, API clients)
- Coordinator data is mocked with realistic weather data structures
- Configuration entries are mocked with proper data structures

### Async Testing

Async methods are tested using pytest-asyncio:

```python
@pytest.mark.asyncio
async def test_async_method(self, mock_coordinator):
    # Test async functionality
    result = await entity.async_forecast_daily()
    assert result == expected_forecast
```

### Exception Testing

Error conditions are tested using pytest's exception handling:

```python
with pytest.raises(UpdateFailed) as exc_info:
    await coordinator._async_update_data()
assert "No weather data found" in str(exc_info.value)
```

## Best Practices Applied

1. **Comprehensive Coverage** - Tests cover happy path, edge cases, and error conditions
2. **Isolation** - Each test is independent and doesn't rely on external systems
3. **Realistic Data** - Mock data structures match real API responses
4. **Clear Naming** - Test names clearly describe what is being tested
5. **Documentation** - Each test has a descriptive docstring
6. **Parametrization** - Different scenarios are tested systematically
7. **Async Handling** - Proper async/await patterns for async methods

## Adding New Tests

When adding new functionality to the integration:

1. Add corresponding test methods to the appropriate test class
2. Use existing fixtures where possible
3. Follow the naming convention: `test_<functionality>_<scenario>`
4. Include both positive and negative test cases
5. Update this documentation if new test patterns are introduced

## Configuration

Test configuration is managed in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-v --tb=short --strict-markers"
testpaths = ["tests"]
asyncio_mode = "auto"
```
