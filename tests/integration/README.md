# Integration Tests

Integration tests verify end-to-end functionality of the stack graph library, including graph construction and reference resolution.

## Structure

```
integration/
├── base/                    # Base classes for multi-language testing
│   ├── base_resolution_tests.py
│   ├── base_graph_tests.py
│   └── README.md
└── python/                  # Python-specific tests
    ├── test_resolution_*.py
    └── test_python_*.py
```

## Base Classes

The `base/` directory provides abstract base classes that language-specific test suites should inherit from:

- **`BaseResolutionTestSuite`**: For reference resolution tests
- **`BaseGraphTestSuite`**: For graph construction tests

These classes provide:
- Standardized helper methods
- Common assertion utilities
- Consistent test patterns

See `base/README.md` for detailed documentation.

## Test Categories

### Resolution Tests (`test_resolution_*.py`)

Test reference resolution across various scenarios:

- **`test_resolution_basic.py`**: Basic resolution (variables, parameters, scoping)
- **`test_resolution_functions.py`**: Function-related resolution (lambdas, closures, parameters)
- **`test_resolution_classes.py`**: Class-related resolution (methods, attributes, inheritance)
- **`test_resolution_imports.py`**: Import resolution
- **`test_resolution_scoping.py`**: Advanced scoping (global, nonlocal, closures)
- **`test_resolution_control_flow.py`**: Control flow constructs (loops, conditionals)
- **`test_resolution_comprehensions.py`**: List/dict/set comprehensions
- **`test_resolution_expressions.py`**: Complex expressions (walrus operator, chained calls)
- **`test_resolution_pattern_matching.py`**: Pattern matching (Python 3.10+)
- **`test_resolution_edge_cases.py`**: Edge cases and error handling
- **`test_resolution_performance.py`**: Performance and scalability
- **`test_resolution_validation.py`**: Algorithm correctness and invariants

### Graph Construction Tests (`test_python_*.py`)

Test stack graph construction:

- **`test_python_complete.py`**: Complete examples with various Python features
- **`test_python_extended.py`**: Extended features and edge cases
- **`test_stack_graph_builder.py`**: Builder API and file handling

## Running Integration Tests

```bash
# All integration tests
pytest tests/integration/

# Python tests only
pytest tests/integration/python/

# Specific category
pytest tests/integration/python/test_resolution_basic.py

# With verbose output
pytest -v tests/integration/
```

## Writing Integration Tests

### Using Base Classes

```python
from tests.integration.base import BaseResolutionTestSuite

class TestMyLanguageResolution(BaseResolutionTestSuite):
    def get_language(self):
        return "mylanguage"
    
    def test_resolve_variable(self):
        code = "x = 1\nprint(x)"
        roots = self.build_graph(code)
        results = self.resolve_reference(roots, "x")
        self.assert_resolution_success(results, "x")
```

### Direct Testing (Without Base Classes)

```python
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from tests.conftest import get_all_nodes

def test_resolve_variable():
    code = "x = 1\nprint(x)"
    builder = StackGraphBuilder()
    roots = builder.build_from_code(code)
    
    resolver = ReferenceResolver()
    all_nodes = get_all_nodes(roots)
    push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
    
    assert len(push_nodes) > 0
    results = resolver.resolve(push_nodes[0], roots)
    assert len(results) > 0
    assert results[0].definition.symbol == 'x'
```

## Test Patterns

### Pattern 1: Basic Resolution

```python
def test_resolve_local_variable(self):
    code = "x = 1\nprint(x)"
    roots = self.build_graph(code)
    results = self.resolve_reference(roots, "x")
    self.assert_resolution_success(results, "x")
```

### Pattern 2: Multiple References

```python
def test_multiple_references(self):
    code = "x = 10\ny = x + 5\nz = x * 2"
    roots = self.build_graph(code)
    self.assert_all_references_resolve_to_same(roots, "x")
```

### Pattern 3: Graph Structure

```python
def test_graph_structure(self):
    code = "class A:\n    def method(self): pass"
    roots = self.build_graph(code)
    self.assert_graph_not_empty(roots, min_nodes=5)
    self.assert_scope_structure(roots, min_scopes=1)
    self.assert_graph_consistency(roots)
```

## Best Practices

1. **Use base classes** when possible for consistency
2. **Test both success and failure cases**
3. **Verify graph consistency** in complex tests
4. **Use descriptive test names** that explain what is being tested
5. **Add docstrings** explaining the test scenario
6. **Test edge cases**: empty code, undefined references, deeply nested structures
7. **Verify specific properties**: not just existence but correctness

## Adding Tests for New Languages

1. Create `tests/integration/<language>/` directory
2. Create test files inheriting from base classes
3. Implement `get_language()` method
4. Add language-specific test cases
5. Follow patterns from Python tests
6. Document language-specific considerations

## Performance Considerations

- Performance tests should verify reasonable execution times
- Use `max_depth` and `max_paths` limits appropriately
- Test with various graph sizes
- Monitor for memory leaks in long-running tests
