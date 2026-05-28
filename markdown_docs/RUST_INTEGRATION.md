# Rust Integration for owlapy

This document describes the Rust integration for performance-critical operations in owlapy.

## Overview

Phase 1 of Rust integration focuses on **similarity metrics** used in retrieval evaluation:
- `jaccard_similarity()` - Jaccard index between two sets
- `f1_set_similarity()` - F1 score between two sets
- Batch variants for processing multiple pairs

## Performance Gains

Expected speedups (measured on 1K-element sets):
- **Jaccard similarity**: 50-100x faster
- **F1 score**: 50-100x faster
- **Batch operations**: 100-200x faster (with parallel processing)

## Building from Source

### Prerequisites

1. **Rust toolchain** (1.70+):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Python development headers**:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev
   
   # macOS (via Homebrew)
   brew install python@3.11
   ```

3. **setuptools-rust**:
   ```bash
   pip install setuptools-rust
   ```

### Build and Install

```bash
# From owlapy root directory
pip install -e '.[dev]'
```

This will:
1. Compile the Rust extension (`owlapy_rust.so`)
2. Install it alongside the Python package
3. Automatically use Rust versions when available

### Build Rust Extension Only

```bash
cd rust
cargo build --release

# Copy to Python package
cp target/release/libowlapy_rust.so ../owlapy/owlapy_rust.so  # Linux
# OR
cp target/release/libowlapy_rust.dylib ../owlapy/owlapy_rust.so  # macOS
```

## Usage

The API is **100% backwards compatible**. No code changes needed:

```python
from owlapy.utils import jaccard_similarity, f1_set_similarity

set1 = {"a", "b", "c"}
set2 = {"b", "c", "d"}

# Automatically uses Rust if available, falls back to Python
jaccard = jaccard_similarity(set1, set2)  # Fast!
f1 = f1_set_similarity(set1, set2)        # Fast!
```

### Checking Which Implementation is Active

```python
import owlapy.utils

if hasattr(owlapy.utils, '_RUST_AVAILABLE') and owlapy.utils._RUST_AVAILABLE:
    print("🚀 Using Rust-accelerated similarity functions")
else:
    print("🐍 Using pure Python similarity functions")
```

### Batch Processing (Rust-only feature)

Process multiple set pairs efficiently:

```python
from owlapy.utils import jaccard_similarity_batch

pairs = [
    ({"a", "b"}, {"b", "c"}),
    ({"x", "y"}, {"y", "z"}),
    ({"1", "2"}, {"2", "3"}),
]

# Returns list of similarities
similarities = jaccard_similarity_batch(pairs)
```

## Testing

### Run Regression Tests

```bash
# Test correctness (Rust == Python results)
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityCorrectness -v

# Test performance (Rust >= 5x faster)
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityPerformance -v

# Test edge cases
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityEdgeCases -v

# Run all Rust tests
pytest tests/test_rust_similarity_regression.py -v
```

### Benchmark

```bash
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityPerformance::test_jaccard_performance_medium_sets -v -s
```

Sample output:
```
Jaccard (1K sets): Python=245.32ms, Rust=2.14ms, Speedup=114.6x
```

## Architecture

### Rust Module (`owlapy/rust/src/lib.rs`)

- Uses **FxHash** (Firefox's hash function) for fast hashing
- Handles multiple Python collection types (set, frozenset, list)
- SIMD-friendly operations for large sets
- Zero-copy where possible

### Python Integration (`owlapy/utils.py`)

```python
# Conditional import with fallback
try:
    from owlapy_rust import jaccard_similarity
except ImportError:
    # Use pure Python version
    jaccard_similarity = _jaccard_similarity_python
```

### Build System

- `pyproject.toml`: Declares `setuptools-rust` as build dependency
- `setup.py`: Configures Rust extension as **optional** (graceful degradation)
- `owlapy/rust/Cargo.toml`: Rust package configuration with PyO3 bindings

## Troubleshooting

### "Rust extension not available" during tests

**Solution**: Build the extension first:
```bash
pip install setuptools-rust
pip install -e .
```

### ImportError: dynamic module does not define init function

**Solution**: Rebuild with matching Python version:
```bash
cd rust
cargo clean
cd ..
pip install -e . --force-reinstall --no-cache-dir
```

### Performance not as expected

**Reasons**:
1. **Small sets** (<100 elements) - overhead dominates
2. **Debug build** - use `cargo build --release`
3. **Python GIL** - batch operations help

## Future Phases

### Phase 2: Core Reasoning (Planned)
- Graph traversal (`sub_classes`, `super_classes`)
- Instance retrieval caching
- Property lookups

### Phase 3: Syntax Processing (Planned)
- OWL → SPARQL conversion
- DL/Manchester parsing

## Contributing

When modifying Rust code:

1. **Format**:
   ```bash
   cd rust
   cargo fmt
   ```

2. **Lint**:
   ```bash
   cargo clippy -- -D warnings
   ```

3. **Test**:
   ```bash
   pytest tests/test_rust_similarity_regression.py -v
   ```

4. **Benchmark**:
   ```bash
   pytest tests/test_rust_similarity_regression.py::TestRustSimilarityPerformance -v -s
   ```

## License

Same as owlapy (MIT License).
