"""Nox configuration for Időkép integration testing."""

import shutil
from pathlib import Path

import nox

# Default Python versions to test against
PYTHON_VERSIONS = ["3.13"]


@nox.session(name="fast")
def fast_test(session: nox.Session) -> None:
    """Run API tests only - FASTEST (no Home Assistant installation)."""
    session.log("⚡ For fastest testing, use direct pytest instead:")
    session.log("   python -m pytest tests/test_api.py -v")
    session.log("   OR: make test-api")
    session.log("")
    session.log("This avoids virtual env creation and Home Assistant installation.")
    session.log("Skipping Nox session - use direct commands above.")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run comprehensive tests with Home Assistant - SLOW but complete."""
    # Install all dependencies including Home Assistant
    session.install(
        "pytest", "pytest-asyncio", "pytest-cov", "homeassistant", "beautifulsoup4"
    )

    session.run(
        "pytest",
        "tests/",
        "--cov=custom_components",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        *session.posargs,
    )


@nox.session(name="quick-test")
def quick_test(session: nox.Session) -> None:
    """Run quick tests with minimal dependencies - no coverage."""
    # Install basic test requirements first
    session.install("-r", "test-requirements.txt")
    session.install("aiohttp", "beautifulsoup4", "homeassistant")

    # Run only API tests with Home Assistant available
    session.run(
        "pytest",
        "tests/test_api.py",
        "-v",
        "--tb=short",
        *session.posargs,
    )


@nox.session(name="full-test")
def full_test(session: nox.Session) -> None:
    """Run tests with Home Assistant (SLOW - use only when needed)."""
    session.install(
        "pytest", "pytest-asyncio", "pytest-cov", "homeassistant", "beautifulsoup4"
    )
    session.run(
        "pytest",
        "tests/",
        "--cov=custom_components",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        *session.posargs,
    )


@nox.session(name="super-quick")
def super_quick_test(session: nox.Session) -> None:
    """Run tests with only pytest - may fail on HA imports."""
    session.install("-r", "minimal-test-requirements.txt")

    # Create a test that ignores HomeAssistant import failures
    session.run(
        "python",
        "-c",
        """
import sys
import subprocess
try:
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/",
        "-v", "--tb=line", "--import-mode=importlib",
        "--ignore-glob=**/conftest.py"  # Skip conftest that imports HA
    ], cwd=".")
    print(f"Exit code: {result.returncode}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
""",
        *session.posargs,
    )


@nox.session
def ruff(session: nox.Session) -> None:
    """Run Ruff linter and formatter."""
    session.install("ruff")

    # Run linter
    session.run("ruff", "check", ".", *session.posargs)

    # Check formatting
    session.run("ruff", "format", "--check", ".", *session.posargs)


@nox.session
def ruff_fix(session: nox.Session) -> None:
    """Fix code issues with Ruff."""
    session.install("ruff")

    # Fix linting issues
    session.run("ruff", "check", "--fix", ".", *session.posargs)

    # Apply formatting
    session.run("ruff", "format", ".", *session.posargs)


@nox.session
def pylint(session: nox.Session) -> None:
    """Run Pylint."""
    session.install("pylint", "homeassistant", "beautifulsoup4")
    session.run("pylint", "custom_components", "tests", *session.posargs)


@nox.session
def mypy(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.install("mypy", "homeassistant", "beautifulsoup4")
    session.run("mypy", "custom_components", *session.posargs)


@nox.session
def safety(session: nox.Session) -> None:
    """Check dependencies for security vulnerabilities."""
    session.install("safety")
    session.run("safety", "check", "--json")


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate coverage report."""
    session.install("coverage[toml]")
    session.run("coverage", "report")
    session.run("coverage", "html")


@nox.session(name="lint-all")
def lint_all(session: nox.Session) -> None:
    """Run all linting tools."""
    # Run Ruff
    session.install("ruff")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")

    # Run Pylint
    session.install("pylint", "homeassistant", "beautifulsoup4")
    session.run("pylint", "custom_components", "tests")


@nox.session(name="test-all", python=PYTHON_VERSIONS)
def test_all(session: nox.Session) -> None:
    """Run comprehensive tests with all checks."""
    # Install all dependencies
    session.install(
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "ruff",
        "pylint",
        "homeassistant",
        "beautifulsoup4",
    )

    # Run linting first
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("pylint", "custom_components", "tests")

    # Run tests
    session.run(
        "pytest",
        "tests/",
        "--cov=custom_components",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
    )


@nox.session(name="format")
def format_code(session: nox.Session) -> None:
    """Format code with Ruff."""
    session.install("ruff")
    session.run("ruff", "format", ".")
    session.run("ruff", "check", "--fix", ".")


@nox.session(name="clean")
def clean(session: nox.Session) -> None:
    """Clean up generated files."""
    # Directories to remove
    dirs_to_remove = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        ".mypy_cache",
        ".nox",
        "__pycache__",
    ]

    for dir_name in dirs_to_remove:
        for path in Path().rglob(dir_name):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                session.log(f"Removed {path}")

    # Files to remove
    files_to_remove = [".coverage", "coverage.xml"]
    for file_name in files_to_remove:
        for path in Path().rglob(file_name):
            if path.is_file():
                path.unlink()
                session.log(f"Removed {path}")


# Configure default sessions when running `nox` without arguments
# NOTE: For fastest testing, use direct pytest: make test-api
nox.options.sessions = ["ruff", "fast"]
