.PHONY: help test lint format check-format pylint ruff-check ruff-format all clean coverage nox-test nox-lint nox-all

help:  ## Show this help message
	@echo "🧪 Időkép Integration - Developer Commands"
	@echo "==========================================="
	@echo ""
	@echo "⚡ FASTEST options (for daily development):"
	@echo "  test-api           Run API tests only (~0.5s)"
	@echo "  ruff-check         Super fast linting (~0.1s)"
	@echo ""
	@echo "📋 Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📖 For more details, see:"
	@echo "  - FAST_TESTING_GUIDE.md    (fastest development workflow)"
	@echo "  - TEST_RUNNER_GUIDE.md     (comprehensive testing guide)"

# Direct pytest commands (FASTEST - no virtual env)
test:  ## Run unit tests (direct pytest)
	python -m pytest tests/ -v

test-api:  ## Run API tests only (FASTEST - no Home Assistant)
	python -m pytest tests/test_api.py -v

test-cov:  ## Run tests with coverage
	python -m pytest tests/ --cov=custom_components --cov-report=term-missing --cov-report=html

# Direct ruff commands
ruff-check:  ## Run Ruff linter
	ruff check .

ruff-format:  ## Run Ruff formatter
	ruff format .

check-format:  ## Check if code is formatted correctly
	ruff format --check .

# Direct pylint command
pylint:  ## Run Pylint
	pylint custom_components tests

# Nox commands (recommended)
nox-test:  ## Run tests with Nox (FAST - no Home Assistant)
	nox -s tests

nox-test-full:  ## Run tests with Nox + Home Assistant (SLOW)
	nox -s full-test

nox-quick:  ## Run quick tests with Nox (no coverage)
	nox -s quick-test

nox-super-quick:  ## Run super quick tests with Nox (minimal deps)
	nox -s super-quick

nox-lint-fast:  ## Run fast linting with Nox (Ruff only)
	nox -s ruff

nox-lint:  ## Run all linting with Nox
	nox -s lint-all

nox-ruff:  ## Run Ruff with Nox
	nox -s ruff

nox-fix:  ## Fix code issues with Nox
	nox -s ruff_fix

nox-all:  ## Run comprehensive tests with Nox
	nox -s test-all

nox-clean:  ## Clean up with Nox
	nox -s clean

# Legacy commands
lint: ruff-check pylint  ## Run all linters (direct)
format: ruff-format  ## Format code (direct)
all: lint test  ## Run all checks and tests (direct)

clean:  ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .nox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

coverage: test-cov  ## Generate coverage report
	@echo "Coverage report generated in htmlcov/index.html"

ci: nox-all  ## Run CI pipeline with Nox (recommended)
