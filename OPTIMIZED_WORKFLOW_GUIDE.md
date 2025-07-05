# Optimized Test and Lint Workflow Guide

## Summary

We've successfully set up a comprehensive, modern test and lint workflow for the Időkép Home Assistant integration. Here's what's been implemented and how to use it effectively.

## Quick Commands (Fastest Feedback)

### 1. **Super Fast Linting** ⚡ (~2-3 seconds)
```bash
# Using Nox (recommended)
nox -s ruff
# Or using Make
make nox-lint-fast
# Or directly
ruff check .
```

### 2. **Auto-fix Code Issues** 🔧 (~3-5 seconds)
```bash
nox -s ruff_fix
# Or
make nox-fix
```

### 3. **Direct pytest** (if HA is already installed) ⚡ (~5-10 seconds)
```bash
# If you have homeassistant installed in current environment
python -m pytest tests/ -v
```

## Medium Speed Commands

### 4. **Comprehensive Linting** (~30-60 seconds)
```bash
nox -s lint-all  # Runs Ruff + Pylint
```

### 5. **Tests with Home Assistant** (~2-3 minutes first time, ~30-60s cached)
```bash
nox -s quick-test  # Tests without coverage
nox -s tests       # Full tests with coverage
```

## Comprehensive Commands

### 6. **Everything** (~3-5 minutes)
```bash
nox -s test-all    # All linting + testing
make nox-all
```

## File Structure

```
/workspaces/HA-Idokep/
├── pyproject.toml              # Unified tool configuration
├── noxfile.py                  # Nox sessions (main workflow)
├── Makefile                    # Quick shortcuts
├── test-requirements.txt       # Minimal test dependencies
├── minimal-test-requirements.txt # Super minimal deps
├── TEST_RUNNER_GUIDE.md       # This file
├── tests/
│   ├── conftest.py            # Pytest fixtures with HA
│   ├── conftest_mock.py       # Mock fixtures (no HA needed)
│   ├── test_weather.py        # Weather entity tests
│   ├── test_coordinator.py    # Coordinator tests
│   └── README.md              # Test documentation
└── custom_components/idokep/   # Source code
```

## Workflow Recommendations

### For Development (Fast Feedback Loop)

1. **Start with linting** (always fast):
   ```bash
   nox -s ruff
   ```

2. **Fix auto-fixable issues**:
   ```bash
   nox -s ruff_fix
   ```

3. **Run tests when ready**:
   ```bash
   # If HA already installed in your environment:
   python -m pytest tests/ -v

   # Otherwise (will install HA - slower first time):
   nox -s quick-test
   ```

### For CI/CD or Comprehensive Checks

```bash
nox -s test-all
```

### For Pull Requests

```bash
# Check everything is clean
nox -s ruff
nox -s tests
```

## Nox Sessions Available

| Session | Speed | Purpose |
|---------|-------|---------|
| `ruff` | ⚡⚡⚡ | Fast linting only |
| `ruff_fix` | ⚡⚡⚡ | Auto-fix issues |
| `quick-test` | ⚡⚡ | Tests without coverage |
| `tests` | ⚡ | Full tests with coverage |
| `lint-all` | ⚡ | All linting tools |
| `test-all` | 🐌 | Everything comprehensive |
| `pylint` | 🐌 | Pylint only (slow) |
| `mypy` | 🐌 | Type checking |
| `safety` | ⚡ | Security check |
| `clean` | ⚡ | Clean up files |

## Why Home Assistant Installation is Slow

The main bottleneck is installing Home Assistant (500+ dependencies, ~200MB). Solutions implemented:

1. **Separate sessions**: Fast linting doesn't need HA
2. **Pip caching**: Second installs are faster
3. **Minimal dependencies**: Only install what's needed per session
4. **Quick shortcuts**: Direct pytest if HA already available

## Configuration Files

### pyproject.toml
- Unified configuration for pytest, ruff, pylint, coverage
- Modern Python packaging standards

### noxfile.py
- Multiple test environments and Python versions
- Separate sessions for different speed/thoroughness needs
- Automatic dependency management

### Makefile
- Simple shortcuts for common tasks
- Both direct commands and Nox-based workflows

## Best Practices

1. **Use `nox -s ruff` frequently** - it's always fast
2. **Fix issues with `nox -s ruff_fix`** - auto-fixes many problems
3. **Run `nox -s quick-test` when you need test validation**
4. **Use `nox -s test-all` before pushing** - comprehensive check
5. **Keep environments clean with `nox -s clean`**

## Coverage and Reports

- HTML coverage reports generated in `htmlcov/`
- Pytest generates detailed test reports
- Ruff provides actionable lint suggestions

## Troubleshooting

### "Home Assistant taking too long to install"
- Use `nox -s ruff` for quick feedback while developing
- Once HA is installed in an environment, reuse that environment
- Consider using `python -m pytest` directly if HA is available

### "Tests failing due to missing dependencies"
- Use the full `nox -s tests` session
- Check if all test requirements are in `test-requirements.txt`

### "Lint errors are overwhelming"
- Start with `nox -s ruff_fix` to auto-fix simple issues
- Address remaining issues one by one
- Use `ruff check --fix` for ongoing development

This workflow provides both fast feedback for development and comprehensive validation for production-ready code.
