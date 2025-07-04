#!/usr/bin/env python3
"""Fast test runner that tries to avoid slow Home Assistant installation."""

import subprocess
import sys
from pathlib import Path

try:
    import homeassistant  # noqa: F401

    HOMEASSISTANT_AVAILABLE = True
except ImportError:
    HOMEASSISTANT_AVAILABLE = False


def check_homeassistant_available() -> bool:
    """Check if Home Assistant is already available in the current environment."""
    return HOMEASSISTANT_AVAILABLE


def run_fast_tests() -> int:
    """Run tests with the fastest method available."""
    print("🚀 Fast Test Runner for Időkép Integration")
    print("=" * 50)

    if check_homeassistant_available():
        print("✅ Home Assistant found in current environment")
        print("📝 Running pytest directly...")

        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

        try:
            result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent)
        except KeyboardInterrupt:
            print("\n⚠️  Test run cancelled by user")
            return 1
        else:
            return result.returncode

    else:
        print("⚠️  Home Assistant not found in current environment")
        print("🔄 Falling back to Nox with quick-test session...")
        print("📌 This will install Home Assistant (may take 2-3 minutes first time)")

        cmd = ["nox", "-s", "quick-test"]

        try:
            result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent)
            return result.returncode
        except KeyboardInterrupt:
            print("\n⚠️  Test run cancelled by user")
            return 1
        except FileNotFoundError:
            print("❌ Nox not found. Please install nox: pip install nox")
            print("💡 Or install Home Assistant: pip install homeassistant")
            return 1


if __name__ == "__main__":
    exit_code = run_fast_tests()

    if exit_code == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    sys.exit(exit_code)
