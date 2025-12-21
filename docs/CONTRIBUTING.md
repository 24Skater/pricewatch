# Contributing to Pricewatch

Thank you for your interest in contributing to Pricewatch! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Running Tests](#running-tests)
- [Submitting Changes](#submitting-changes)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerized development)

### Finding Issues

- Look for issues labeled `good first issue` for beginner-friendly tasks
- Check `help wanted` labels for issues needing community assistance
- Review the [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) for planned enhancements

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pricewatch.git
   cd pricewatch
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Initialize Database**
   ```bash
   alembic upgrade head
   ```

6. **Install Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

7. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Maximum line length: 100 characters
- Use type hints for all function parameters and return values

### Formatting

We use Ruff for code formatting. Run before committing:

```bash
ruff format app/ tests/
ruff check app/ tests/ --fix
```

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
    """
```

## Running Tests

### Full Test Suite

```bash
pytest tests/ -v
```

### With Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

### Specific Test Categories

```bash
# Security tests
pytest tests/test_security.py -v

# Integration tests
pytest tests/test_integration.py -v

# Scraper tests
pytest tests/test_scraper.py -v
```

### Pre-commit Checks

```bash
pre-commit run --all-files
```

## Submitting Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Workflow

1. Create a new branch from `main`
2. Make your changes
3. Write/update tests as needed
4. Run the test suite
5. Run pre-commit hooks
6. Push and create a pull request

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(scraper): add support for meta tag price extraction

fix(notifications): handle SMTP timeout gracefully

docs(readme): update installation instructions

test(security): add CSRF protection tests
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code is formatted with Ruff
3. ✅ No linting errors
4. ✅ Pre-commit hooks pass
5. ✅ Documentation updated if needed
6. ✅ CHANGELOG.md updated for significant changes

### PR Description

Use the pull request template and include:

- Clear description of changes
- Link to related issue(s)
- Screenshots for UI changes
- Test plan or testing notes

### Review Process

1. At least one maintainer approval required
2. All CI checks must pass
3. No unresolved review comments
4. Branch is up-to-date with `main`

### After Merge

- Delete your feature branch
- Verify the change in the main branch

## Questions?

- Open a [Discussion](https://github.com/pricewatch/pricewatch/discussions)
- Check existing [Issues](https://github.com/pricewatch/pricewatch/issues)
- Review the [Documentation](README.md)

---

Thank you for contributing to Pricewatch! 🎉

