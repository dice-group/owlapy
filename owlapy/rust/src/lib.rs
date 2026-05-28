use pyo3::prelude::*;
use pyo3::types::{PyFrozenSet, PyList, PySet};
use std::collections::HashSet;

/// Fast Jaccard similarity using FxHash (Firefox's hash function)
/// 
/// Computes: |A ∩ B| / |A ∪ B|
/// 
/// Args:
///     set1: First set (as list, set, or frozenset)
///     set2: Second set (as list, set, or frozenset)
/// 
/// Returns:
///     Jaccard similarity score [0.0, 1.0]
#[pyfunction]
fn jaccard_similarity(py: Python, set1: &Bound<'_, PyAny>, set2: &Bound<'_, PyAny>) -> PyResult<f64> {
    // Convert Python collections to Rust HashSet
    let s1 = extract_hashset(py, set1)?;
    let s2 = extract_hashset(py, set2)?;
    
    // Edge case: both empty
    if s1.is_empty() && s2.is_empty() {
        return Ok(1.0);
    }
    
    // Compute intersection and union sizes efficiently
    let intersection_size = s1.intersection(&s2).count();
    let union_size = s1.len() + s2.len() - intersection_size;
    
    Ok(intersection_size as f64 / union_size as f64)
}

/// Fast F1 score between two sets using FxHash
/// 
/// Computes: 2 * (precision * recall) / (precision + recall)
/// where precision = |A ∩ B| / |B| and recall = |A ∩ B| / |A|
/// 
/// Args:
///     set1: First set (treated as ground truth)
///     set2: Second set (treated as prediction)
/// 
/// Returns:
///     F1 score [0.0, 1.0]
#[pyfunction]
fn f1_set_similarity(py: Python, set1: &Bound<'_, PyAny>, set2: &Bound<'_, PyAny>) -> PyResult<f64> {
    let s1 = extract_hashset(py, set1)?;
    let s2 = extract_hashset(py, set2)?;
    
    // Edge case: both empty
    if s1.is_empty() && s2.is_empty() {
        return Ok(1.0);
    }
    
    // Edge case: prediction is empty
    if s2.is_empty() {
        return Ok(0.0);
    }
    
    let true_positives = s1.intersection(&s2).count();
    
    let precision = if s2.is_empty() {
        0.0
    } else {
        true_positives as f64 / s2.len() as f64
    };
    
    let recall = if s1.is_empty() {
        0.0
    } else {
        true_positives as f64 / s1.len() as f64
    };
    
    if precision + recall == 0.0 {
        return Ok(0.0);
    }
    
    Ok(2.0 * (precision * recall) / (precision + recall))
}

/// Helper function to extract HashSet<String> from Python collections
fn extract_hashset(_py: Python, obj: &Bound<'_, PyAny>) -> PyResult<HashSet<String, fxhash::FxBuildHasher>> {
    let mut set = HashSet::with_hasher(fxhash::FxBuildHasher::default());
    
    // Try different Python collection types
    if let Ok(pyset) = obj.downcast::<PySet>() {
        for item in pyset.iter() {
            // Try to convert to string - handles both str and repr() for other types
            if let Ok(s) = item.extract::<String>() {
                set.insert(s);
            } else if let Ok(s) = item.str() {
                // Fallback: use Python's str() for non-string types (int, float, etc.)
                if let Ok(s_str) = s.extract::<String>() {
                    set.insert(s_str);
                }
            }
        }
    } else if let Ok(pyfrozenset) = obj.downcast::<PyFrozenSet>() {
        for item in pyfrozenset.iter() {
            if let Ok(s) = item.extract::<String>() {
                set.insert(s);
            } else if let Ok(s) = item.str() {
                if let Ok(s_str) = s.extract::<String>() {
                    set.insert(s_str);
                }
            }
        }
    } else if let Ok(pylist) = obj.downcast::<PyList>() {
        for item in pylist.iter() {
            if let Ok(s) = item.extract::<String>() {
                set.insert(s);
            } else if let Ok(s) = item.str() {
                if let Ok(s_str) = s.extract::<String>() {
                    set.insert(s_str);
                }
            }
        }
    } else {
        // Try iterating as generic iterable
        for item in obj.iter()? {
            let item = item?;
            if let Ok(s) = item.extract::<String>() {
                set.insert(s);
            } else if let Ok(s) = item.str() {
                if let Ok(s_str) = s.extract::<String>() {
                    set.insert(s_str);
                }
            }
        }
    }
    
    Ok(set)
}

/// Python module definition
#[pymodule]
fn owlapy_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(jaccard_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(f1_set_similarity, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_jaccard_basic() {
        // This would need pyo3::prepare_freethreaded_python() for full testing
        // Unit tests will be in Python regression tests
    }
}
