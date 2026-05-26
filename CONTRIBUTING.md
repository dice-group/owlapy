# Contributing to OWLAPY

Thank you for your interest in contributing to OWLAPY! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/owlapy.git
   cd owlapy
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/dice-group/owlapy.git
   ```

## Development Setup

1. Create a conda environment:
   ```bash
   conda create -n owlapy_dev python=3.11 --no-default-packages
   conda activate owlapy_dev
   ```

2. Install the package in development mode with all dependencies:
   ```bash
   pip install -e '.[all]'
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

4. Download test data:
   ```bash
   wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip
   unzip KGs.zip
   ```

## How to Contribute

### Types of Contributions

- **Bug fixes**: Find and fix bugs in the codebase
- **New features**: Implement new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Examples**: Create example scripts demonstrating features
- **Performance**: Optimize existing code

### Workflow

1. Create a new branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. Keep your branch up to date with upstream:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

4. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a Pull Request on GitHub

## Coding Standards

### Python Style

- Follow PEP 8 guidelines (enforced by ruff)
- Maximum line length: 200 characters
- Use type hints wherever possible
- Write descriptive variable and function names

### Code Quality

Before submitting, ensure your code passes all checks:

```bash
# Run linter
ruff check owlapy --line-length=200

# Run tests
pytest

# Check test coverage
coverage run -m pytest
coverage report -m
```

### Pre-commit Hooks

If you've installed pre-commit hooks, they will automatically run before each commit:

- **ruff**: Code linting and formatting
- Style checks

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names that explain what is being tested
- Aim for high test coverage (target: ≥82%)

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_owlapy.py

# Run with coverage
coverage run -m pytest
coverage report -m

# Ignore slow tests (EBR)
pytest --ignore=tests/test_z_do_last_ebr_retrieval.py
```

## Documentation

### Docstrings

- Use Google-style docstrings for all public functions, classes, and methods
- Include:
  - Brief description
  - Args with types
  - Returns with type
  - Raises (if applicable)
  - Examples (when helpful)

Example:
```python
def owl_expression_to_sparql(expression: OWLClassExpression) -> str:
    """Convert an OWL class expression to a SPARQL query.
    
    Args:
        expression: The OWL class expression to convert.
        
    Returns:
        A SPARQL SELECT query string.
        
    Raises:
        ValueError: If the expression cannot be converted.
        
    Example:
        >>> from owlapy.class_expression import OWLClass
        >>> ce = OWLClass("http://example.com/Person")
        >>> query = owl_expression_to_sparql(ce)
    """
```

### Building Documentation

Documentation is built using Sphinx:

```bash
cd docs
make html
```

## Pull Request Process

1. **Update CHANGELOG.md**: Add your changes under the `[Unreleased]` section

2. **Update documentation**: If you've changed APIs or added features, update relevant docs

3. **Ensure tests pass**: All tests must pass in CI

4. **Code review**: Wait for at least one maintainer to review your PR

5. **Address feedback**: Make requested changes and push updates

6. **Squash commits** (optional): You may be asked to squash commits before merging

### Pull Request Title Format

Use conventional commit format:
- `feat: Add new feature X`
- `fix: Resolve bug in Y`
- `docs: Update documentation for Z`
- `test: Add tests for W`
- `refactor: Improve code structure in V`
- `perf: Optimize performance of U`

## Reporting Bugs

### Before Submitting

- Check if the bug has already been reported in Issues
- Verify it's actually a bug and not a feature
- Collect relevant information (error messages, stack traces, environment)

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- OWLAPY version: [e.g., 1.6.4]

**Additional context**
Any other relevant information.
```

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Clearly describe the feature and its use case
3. Explain why this feature would be valuable to OWLAPY users
4. Provide examples of how it would be used

## Questions?

- Check the [documentation](https://dice-group.github.io/owlapy/usage/main.html)
- Ask on [GitHub Discussions](https://github.com/dice-group/owlapy/discussions) (if enabled)
- Open an issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in:
- CHANGELOG.md for their specific contributions
- GitHub's contributor list

Thank you for contributing to OWLAPY! 🎉
