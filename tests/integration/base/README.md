# Base Test Infrastructure

This directory contains abstract base classes for language-agnostic integration tests.

## Purpose

The base test classes provide:
- **Consistency**: Standardized patterns for all language test suites
- **Reusability**: Common utilities and assertion helpers
- **Extensibility**: Easy addition of new language test suites
- **Maintainability**: Centralized test logic that can be improved once and benefit all languages

## Structure

### `base_resolution_tests.py`

Abstract base class for reference resolution tests. Provides:
- `BaseResolutionTestSuite`: Abstract class that language-specific test suites should inherit from
- Helper methods for finding nodes, resolving references, and asserting results
- Standardized assertion methods for resolution success/failure

**Usage:**
```python
from tests.integration.base import BaseResolutionTestSuite

class TestPythonResolution(BaseResolutionTestSuite):
    def get_language(self):
        return "python"
    
    def test_resolve_variable(self):
        code = "x = 1\nprint(x)"
        roots = self.build_graph(code)
        results = self.resolve_reference(roots, "x")
        self.assert_resolution_success(results, "x")
```

### `base_graph_tests.py`

Abstract base class for graph construction tests. Provides:
- `BaseGraphTestSuite`: Abstract class for testing graph structure
- Helper methods for asserting graph properties
- Standardized checks for graph consistency

**Usage:**
```python
from tests.integration.base import BaseGraphTestSuite

class TestPythonGraph(BaseGraphTestSuite):
    def get_language(self):
        return "python"
    
    def test_build_simple_graph(self):
        code = "x = 1"
        roots = self.build_graph(code)
        self.assert_graph_not_empty(roots)
        self.assert_node_exists(roots, "x")
        self.assert_graph_consistency(roots)
```

## Adding a New Language

To add test support for a new language:

1. Create a new directory: `tests/integration/<language>/`
2. Create test files that inherit from the base classes:
   ```python
   from tests.integration.base import BaseResolutionTestSuite
   
   class TestLanguageResolution(BaseResolutionTestSuite):
       def get_language(self):
           return "<language>"
       
       # Add language-specific tests
   ```
3. Follow the patterns established in the Python test suite
4. Use the helper methods from base classes for consistency

## Best Practices

1. **Always inherit from base classes** for resolution and graph tests
2. **Use helper methods** instead of duplicating logic
3. **Add language-specific tests** that test unique features of the language
4. **Maintain consistency** with existing test patterns
5. **Document edge cases** specific to the language

## Helper Methods

### Resolution Helpers
- `find_push_nodes(roots, symbol)`: Find all PUSH nodes for a symbol
- `find_pop_nodes(roots, symbol)`: Find all POP nodes for a symbol
- `resolve_reference(roots, symbol, index)`: Resolve a reference to definitions
- `assert_resolution_success(results, symbol)`: Assert successful resolution
- `assert_resolution_failure(results)`: Assert failed resolution
- `assert_all_references_resolve_to_same(roots, symbol)`: Assert consistency

### Graph Helpers
- `assert_graph_not_empty(roots, min_nodes)`: Assert graph has nodes
- `assert_node_exists(roots, symbol, type)`: Assert node exists
- `assert_node_count(roots, type, count)`: Assert node count
- `assert_scope_structure(roots, min_scopes)`: Assert scope structure
- `assert_graph_consistency(roots)`: Assert graph consistency

## Future Enhancements

- Add support for multi-file tests
- Add performance benchmarking helpers
- Add regression test utilities
- Add visualization helpers for debugging
