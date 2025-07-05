# Test Runner Recommendations for Időkép Integration

## 🏆 **Recommended: Nox + Make** (Best of both worlds)

**Nox** is the most modern and flexible solution for Python projects. Here's why it's perfect for your needs:

### ✅ **Why Nox?**

1. **Isolated Environments** - Each tool runs in its own virtual environment
2. **Python Native** - Configuration in Python, not YAML/INI
3. **Flexible** - Easy to customize and extend
4. **Fast** - Reuses environments when possible
5. **Multiple Python Versions** - Test against Python 3.11, 3.12, 3.13
6. **Tool Integration** - Perfect for Ruff, Pylint, pytest combination

### 🚀 **Quick Start Commands**

```bash
# Install Nox
pip install nox

# List all available sessions
nox --list

# Run default sessions (ruff + tests)
nox

# Run specific sessions
nox -s ruff              # Linting with Ruff
nox -s tests             # Unit tests with coverage
nox -s lint-all          # All linting tools
nox -s test-all          # Comprehensive testing
nox -s ruff_fix          # Auto-fix code issues
nox -s quick-test        # Fast tests without coverage

# Use Make for convenience
make nox-test           # Run tests
make nox-lint           # Run linting
make nox-all            # Run everything
make nox-fix            # Fix code issues
```

### 📋 **Available Nox Sessions**

| Session | Description | Tools Used |
|---------|-------------|------------|
| `tests` | Unit tests with coverage | pytest, pytest-asyncio, pytest-cov |
| `ruff` | Linting and format checking | ruff |
| `ruff_fix` | Auto-fix issues | ruff |
| `pylint` | Advanced static analysis | pylint |
| `mypy` | Type checking | mypy |
| `safety` | Security vulnerability check | safety |
| `lint-all` | All linting tools | ruff + pylint |
| `test-all` | Comprehensive testing | All tools + tests |
| `quick-test` | Fast tests | pytest (no coverage) |
| `clean` | Clean up generated files | - |

## 🎯 **What Each Tool Does**

### **Ruff** 🔍
- **Linting**: Finds code quality issues, unused imports, style violations
- **Formatting**: Auto-formats code to Python standards
- **Speed**: Extremely fast (written in Rust)
- **Rules**: 160+ linting rules from multiple tools

```bash
# Direct usage
ruff check .              # Check for issues
ruff check --fix .        # Fix auto-fixable issues
ruff format .             # Format code
ruff format --check .     # Check formatting without changes
```

### **Pylint** 🔬
- **Deep Analysis**: More thorough static analysis than Ruff
- **Code Quality**: Detects design issues, complexity problems
- **Scoring**: Provides code quality score
- **Slower**: More comprehensive but takes longer

```bash
# Direct usage
pylint custom_components tests
```

### **Pytest** 🧪
- **Unit Testing**: Runs your actual tests
- **Coverage**: Measures how much code is tested
- **Async Support**: Handles async/await properly

```bash
# Direct usage
pytest tests/ -v                              # Basic tests
pytest tests/ --cov=custom_components         # With coverage
```

## 🔄 **Recommended Workflow**

### **Development Workflow**
```bash
# 1. Quick feedback during development
nox -s ruff_fix          # Fix issues automatically
nox -s quick-test        # Fast test run

# 2. Before committing
nox -s lint-all          # Full linting
nox -s tests             # Tests with coverage

# 3. CI/CD Pipeline
nox -s test-all          # Complete validation
```

### **VS Code Integration**

Add these to your VS Code tasks (`.vscode/tasks.json`):

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Nox: Quick Test",
            "type": "shell",
            "command": "nox",
            "args": ["-s", "quick-test"],
            "group": "test"
        },
        {
            "label": "Nox: Lint",
            "type": "shell",
            "command": "nox",
            "args": ["-s", "ruff"],
            "group": "build"
        },
        {
            "label": "Nox: Fix Code",
            "type": "shell",
            "command": "nox",
            "args": ["-s", "ruff_fix"],
            "group": "build"
        }
    ]
}
```

## 🆚 **Comparison with Alternatives**

| Tool | Pros | Cons | Best For |
|------|------|------|----------|
| **Nox** ✅ | Modern, flexible, Python config | Learning curve | Complex projects |
| **tox** | Mature, stable | INI config, slower | Legacy projects |
| **pre-commit** | Git integration | Limited flexibility | Git hooks only |
| **GitHub Actions** | CI/CD integration | Cloud only | Remote CI |
| **Custom Scripts** | Simple | No isolation | Quick & dirty |

## 🎨 **Example Output**

When you run `nox -s test-all`, you get:

```
nox > Running session test-all-3.13
nox > Creating virtual environment (virtualenv) using python3.13 in .nox/test-all-3-13
nox > python -m pip install pytest pytest-asyncio pytest-cov ruff pylint homeassistant
nox > ruff check .
✅ All linting passed!
nox > ruff format --check .
✅ Code properly formatted!
nox > pylint custom_components tests
✅ Pylint score: 9.2/10
nox > pytest tests/ --cov=custom_components --cov-report=term-missing
========================= 30 passed =========================
Coverage: 94%
nox > Session test-all-3-13 succeeded.
```

## 🔧 **Configuration Files**

All tools are configured in `pyproject.toml`:

- **Pytest**: Test discovery, markers, async mode
- **Ruff**: Linting rules, formatting options
- **Pylint**: Message control, formatting
- **Coverage**: Source paths, exclusions

## 🎯 **Bottom Line**

**Use Nox** for the best experience:

1. **Development**: `nox -s ruff_fix && nox -s quick-test`
2. **Pre-commit**: `nox -s lint-all && nox -s tests`
3. **CI/CD**: `nox -s test-all`
4. **Convenience**: Use the Makefile shortcuts

This gives you the power of Ruff's speed, Pylint's depth, and pytest's testing - all in isolated, reproducible environments!
