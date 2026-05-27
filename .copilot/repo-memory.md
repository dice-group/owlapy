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

## Pull Request Workflow

**CRITICAL: Always run tests BEFORE creating a pull request!**

### Pre-PR Checklist
1. ✅ Run linter and fix issues:
   ```bash
   ruff check owlapy --line-length=200 --fix --unsafe-fixes
   ```

2. ✅ Run full test suite (excluding EBR):
   ```bash
   PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings -x
   ```

3. ✅ Verify no test failures (especially JVM-related tests)

4. ✅ Commit changes with descriptive message

5. ✅ Push to feature branch

6. ✅ Create pull request

### Known Test Issues

**JVM Restart Error in test_sync_ontology.py**
- **Error**: `OSError: JVM cannot be restarted` in `test__eq__`
- **Cause**: JPype cannot restart JVM within same Python process after stopJVM() is called
- **Location**: `tests/test_sync_ontology.py::TestSyncOntology::test__eq__`
- **Status**: Pre-existing issue, not introduced by documentation changes
- **Impact**: Fails in CI when test runs after other JVM-dependent tests
- **Workaround**: Run this test in isolation or fix test isolation issues

**Always verify tests pass locally before creating PR to avoid CI failures.**

## Recent Issues and Learnings

### PR #216: Agent Documentation Fixes (May 2026)
- **What happened**: Created PR without running tests first
- **Result**: CI failed with JVM restart error in test_sync_ontology.py
- **Lesson**: ALWAYS run `pytest tests -x` before creating PR
- **Context**: The JVM restart error is a pre-existing issue unrelated to documentation changes, but it highlighted the importance of running tests before PR creation
- **Fix needed**: Test isolation issue where `test__eq__` creates a new SyncOntology after JVM was stopped by previous tests

### How to Detect Test Issues Before PR
```bash
# Run these commands in sequence before any PR:
ruff check owlapy --line-length=200 --fix --unsafe-fixes  # Fix linting
PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings -x  # Run tests
# Only create PR if both succeed
```
