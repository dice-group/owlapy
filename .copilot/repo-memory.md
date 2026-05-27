# OWLAPY Repository Memory

## Development Environment

**Always use the `temp_owlapy` conda environment:**

```bash
conda activate temp_owlapy
```

This environment should be created with:
```bash
conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
pip install -e '.[dev]'
```

## Running Tests

Always activate the environment before running tests:
```bash
conda activate temp_owlapy && PYTHONPATH=. pytest [test_file] -v -p no:warnings
```

## Common Commands

### Linting
```bash
conda activate temp_owlapy && ruff check owlapy --line-length=200 --fix --unsafe-fixes
```

### Full Test Suite
```bash
conda activate temp_owlapy && PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings
```

### Coverage
```bash
conda activate temp_owlapy && coverage run -m pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings -x
conda activate temp_owlapy && coverage report -m
```
