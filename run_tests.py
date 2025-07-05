#!/usr/bin/env python3
"""Test runner script for Időkép integration."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(*, coverage: bool = True, verbose: bool = True) -> int:
    """Run the test suite."""
    cmd = ["python", "-m", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(
            [
                "--cov=custom_components.idokep",
                "--cov-report=term-missing",
                "--cov-report=html",
            ]
        )

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=False)
    except KeyboardInterrupt:
        print("\nTest run cancelled by user")
        return 1
    else:
        return result.returncode


def main() -> None:
    """Run the main entry point."""
    parser = argparse.ArgumentParser(description="Run Időkép integration tests")
    parser.add_argument(
        "--no-coverage", action="store_true", help="Skip coverage reporting"
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    exit_code = run_tests(coverage=not args.no_coverage, verbose=not args.quiet)

    if exit_code == 0:
        print("\n✅ All tests passed!")
        if not args.no_coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
