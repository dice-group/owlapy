# Quick Start: Building Rust Extensions for owlapy

## Prerequisites

1. **Install Rust** (if not already installed):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   ```

2. **Verify Rust installation**:
   ```bash
   rustc --version  # Should show 1.70+
   cargo --version
   ```

## Build with Rust Extensions

### Option 1: Standard install with Rust (Recommended)

```bash
# Activate your conda environment
conda activate temp_owlapy

# Install setuptools-rust
pip install setuptools-rust

# Install owlapy with Rust extensions
pip install -e '.[dev]' --force-reinstall --no-cache-dir
```

### Option 2: Build Rust extension manually

```bash
cd rust
cargo build --release

# Copy to Python package directory
cp target/release/libowlapy_rust.so ../owlapy/owlapy_rust.so  # Linux
# OR
cp target/release/libowlapy_rust.dylib ../owlapy/owlapy_rust.so  # macOS
```

## Verify Installation

```bash
# Check if Rust extension is loaded
python -c "
import owlapy.utils
if hasattr(owlapy.utils, '_RUST_AVAILABLE') and owlapy.utils._RUST_AVAILABLE:
    print('✅ Rust extension loaded successfully!')
else:
    print('⚠️  Using pure Python fallback')
"
```

## Run Tests

```bash
# Run all Rust regression tests
pytest tests/test_rust_similarity_regression.py -v

# Run only correctness tests
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityCorrectness -v

# Run only performance tests
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityPerformance -v -s
```

## Troubleshooting

### "No module named 'owlapy_rust'"

**Solution**: The Rust extension didn't build. Try:
```bash
pip install setuptools-rust
pip install -e . --force-reinstall --no-cache-dir
```

### Rust not found

**Solution**: Install Rust toolchain:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Build fails on macOS

**Solution**: Install Xcode command line tools:
```bash
xcode-select --install
```

### Build fails on Linux

**Solution**: Install build essentials:
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

## Expected Performance

After successful installation, you should see:

```bash
pytest tests/test_rust_similarity_regression.py::TestRustSimilarityPerformance::test_jaccard_performance_medium_sets -v -s
```

**Expected output**:
```
Jaccard (1K sets): Python=245.32ms, Rust=2.14ms, Speedup=114.6x
PASSED
```

✨ **50-100x faster similarity computations!**

## Without Rust

If you don't want Rust extensions, owlapy still works with pure Python fallback:

```bash
pip install -e '.[dev]'  # Without setuptools-rust
```

All functionality remains the same, just slower for similarity metrics.
