# ⚡ Fast Testing Guide for Időkép Integration

This guide shows you how to get the fastest feedback while developing, without waiting for Home Assistant installation.

## 🚀 Fastest Options (< 1 second)

### Option 1: Direct API Tests (RECOMMENDED)
```bash
# Test only the API client (most critical component)
make test-api
# OR
python -m pytest tests/test_api.py -v
```
**Time: ~0.5 seconds** | **Coverage: 38 API tests** | **No dependencies needed**

### Option 2: Direct Linting
```bash
# Super fast linting
ruff check .
```
**Time: ~0.1 seconds** | **Full codebase coverage**

### Option 3: Combined Fast Check
```bash
# Lint + API tests in under 1 second
ruff check . && make test-api
```
**Time: ~0.6 seconds** | **High confidence in code quality**

## 🐌 Slower Options (when you need them)

### Full Test Suite (with Home Assistant)
```bash
# All tests including weather entity and coordinator
python -m pytest tests/ -v
```
**Time: ~1 second** | **Full coverage: 68 tests**

### Nox with Home Assistant (CI-style)
```bash
# Full virtual environment with Home Assistant
nox -s tests
```
**Time: 2-3 minutes first time, 30 seconds after** | **Complete isolation**

## 📊 Performance Comparison

| Method | Time | Tests | Home Assistant | Virtual Env | Use Case |
|--------|------|-------|----------------|-------------|----------|
| `make test-api` | ~0.5s | 38 API tests | ❌ No | ❌ No | **Daily development** |
| `python -m pytest tests/` | ~1s | 68 all tests | ✅ Yes | ❌ No | Pre-commit check |
| `nox -s tests` | ~30s+ | 68 all tests | ✅ Yes | ✅ Yes | CI/Release |

## 🎯 Recommended Workflow

1. **During development**: Use `make test-api` for instant feedback
2. **Before committing**: Run `python -m pytest tests/ -v` for full coverage
3. **Before releasing**: Run `nox -s tests` for complete validation

## 💡 Why This Is Fast

- **No Home Assistant installation**: API tests run independently
- **No virtual environment**: Uses your current Python environment
- **Focused testing**: Only tests the most critical component (API client)
- **Minimal dependencies**: Only pytest, aiohttp, and beautifulsoup4

## 🔧 Available Commands

```bash
# Testing
make test-api      # Fastest: API tests only
make test          # Fast: All tests
make test-cov      # Coverage report
nox -s tests       # Comprehensive with HA

# Linting
ruff check .       # Super fast linting
make lint          # All linters
nox -s ruff        # Ruff via Nox

# Combined
make ci            # Full CI pipeline (slow)
nox                # Default: ruff + fast guide
```

## ⚠️ Important Notes

- The API client (`custom_components/idokep/api.py`) is the most critical component
- API tests cover 38 test cases including error handling, scraping, and edge cases
- Weather entity and coordinator tests require Home Assistant imports
- For production/CI, always run the full test suite with Home Assistant

---

**TL;DR**: Use `make test-api` for daily development (0.5s), `python -m pytest tests/` before commits (1s).
