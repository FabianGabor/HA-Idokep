#!/usr/bin/env python3
"""Comprehensive test runner for Időkép integration."""

import argparse
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{description}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, cwd=Path(__file__).parent
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        success = result.returncode == 0
        status_color = Colors.GREEN if success else Colors.RED
        status_text = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status_color}{status_text}{Colors.END}")

        return success, result.stdout + result.stderr

    except Exception as e:
        print(f"{Colors.RED}Error running command: {e}{Colors.END}")
        return False, str(e)


def main() -> None:
    """Return the main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive checks")
    parser.add_argument("--skip-ruff", action="store_true", help="Skip Ruff checks")
    parser.add_argument("--skip-pylint", action="store_true", help="Skip Pylint")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unit tests")
    parser.add_argument("--coverage", action="store_true", help="Include coverage")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues where possible"
    )

    args = parser.parse_args()

    results = []
    total_checks = 0

    print(f"{Colors.BOLD}🧪 Időkép Integration Test Runner{Colors.END}")

    # Ruff checks
    if not args.skip_ruff:
        total_checks += 1
        if args.fix:
            success, _ = run_command(
                ["ruff", "check", "--fix", "."], "🔧 Running Ruff linter (with fixes)"
            )
        else:
            success, _ = run_command(["ruff", "check", "."], "🔍 Running Ruff linter")
        results.append(("Ruff Linting", success))

        # Format check
        total_checks += 1
        if args.fix:
            success, _ = run_command(
                ["ruff", "format", "."], "🎨 Running Ruff formatter"
            )
        else:
            success, _ = run_command(
                ["ruff", "format", "--check", "."], "🎨 Checking code formatting"
            )
        results.append(("Code Formatting", success))

    # Pylint
    if not args.skip_pylint:
        total_checks += 1
        success, _ = run_command(
            ["pylint", "custom_components", "tests"], "🔍 Running Pylint"
        )
        results.append(("Pylint", success))

    # Unit tests
    if not args.skip_tests:
        total_checks += 1
        if args.coverage:
            success, _ = run_command(
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/",
                    "--cov=custom_components",
                    "--cov-report=term-missing",
                    "--cov-report=html",
                    "-v",
                ],
                "🧪 Running unit tests with coverage",
            )
        else:
            success, _ = run_command(
                ["python", "-m", "pytest", "tests/", "-v"], "🧪 Running unit tests"
            )
        results.append(("Unit Tests", success))

    # Summary
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}📊 SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")

    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed

    for check_name, success in results:
        status = (
            f"{Colors.GREEN}✅ PASSED{Colors.END}"
            if success
            else f"{Colors.RED}❌ FAILED{Colors.END}"
        )
        print(f"  {check_name:<20} {status}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total_checks} checks passed{Colors.END}")

    if failed > 0:
        print(f"\n{Colors.RED}❌ {failed} check(s) failed{Colors.END}")
        if args.coverage and not args.skip_tests:
            print(
                f"{Colors.YELLOW}📊 Coverage report available at htmlcov/index.html{Colors.END}"
            )
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}🎉 All checks passed!{Colors.END}")
        if args.coverage and not args.skip_tests:
            print(
                f"{Colors.GREEN}📊 Coverage report generated at htmlcov/index.html{Colors.END}"
            )


if __name__ == "__main__":
    main()
