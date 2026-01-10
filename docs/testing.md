# Testing Guide

Complete guide to testing in the Mycelium stack graphs library.

## Overview

The Mycelium test suite is designed to be:
- **Comprehensive**: Covering basic features, edge cases, and performance
- **Reusable**: Base classes enable consistent testing across languages
- **Maintainable**: Clear structure, documentation, and patterns
- **Extensible**: Easy to add tests for new languages

## Test Structure

```
tests/
├── README.md                 # Test suite overview
├── conftest.py               # Shared fixtures and helpers
├── unit/                     # Unit tests
│   ├── test_models.py
│   ├── test_graph_builder.py
│   ├── test_captures_manager.py
│   └── test_python_handlers.py
└── integration/             # Integration tests
    ├── base/                 # Base classes for multi-language tests
    │   ├── base_resolution_tests.py
    │   ├── base_graph_tests.py
    │   └── README.md
    └── python/               # Python-specific tests
        ├── test_resolution_*.py
        ├── test_python_*.py
        └── README.md
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific directory
pytest tests/unit/
pytest tests/integration/

# Run specific file
pytest tests/integration/python/test_resolution_basic.py

# Run specific test
pytest tests/integration/python/test_resolution_basic.py::TestBasicResolution::test_resolve_local_variable
```

### With Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage in terminal
pytest --cov=src --cov-report=term-missing
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Writing Tests

### Unit Tests

Unit tests focus on individual components:

```python
def test_gnode_creation():
    """Test basic GNode creation."""
    node = GNode(
        symbol="test",
        type="SCOPE",
        start_byte=0,
        end_byte=10
    )
    
    assert node.symbol == "test"
    assert node.type == "SCOPE"
    assert node.start_byte == 0
    assert node.end_byte == 10
```

### Integration Tests Using Base Classes

For language-specific tests, inherit from base classes:

```python
from tests.integration.base import BaseResolutionTestSuite

class TestPythonResolution(BaseResolutionTestSuite):
    def get_language(self):
        return "python"
    
    def test_resolve_variable(self):
        """Test resolving a variable reference."""
        code = "x = 1\nprint(x)"
        roots = self.build_graph(code)
        results = self.resolve_reference(roots, "x")
        self.assert_resolution_success(results, "x")
```

### Integration Tests Without Base Classes

For direct testing:

```python
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from tests.conftest import get_all_nodes, assert_graph_structure_valid

def test_resolve_variable():
    """Test resolving a variable reference."""
    code = "x = 1\nprint(x)"
    builder = StackGraphBuilder()
    roots = builder.build_from_code(code)
    
    resolver = ReferenceResolver()
    all_nodes = get_all_nodes(roots)
    push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
    
    assert len(push_nodes) > 0, "Should find PUSH node"
    results = resolver.resolve(push_nodes[0], roots)
    assert len(results) > 0, "Should find definition"
    assert results[0].definition.symbol == 'x'
    
    # Verify graph consistency
    assert_graph_structure_valid(roots)
```

## Helper Functions

### From `conftest.py`

**Node Finding:**
- `find_node_by_symbol(nodes, symbol)`: Find node by symbol
- `find_nodes_by_type(nodes, node_type)`: Find all nodes of type
- `find_nodes_by_symbol_and_type(nodes, symbol, node_type)`: Find by symbol and type
- `get_all_nodes(nodes)`: Get all nodes as flat list

**Counting:**
- `count_nodes_by_type(nodes, node_type)`: Count nodes by type
- `count_references_to_symbol(nodes, symbol)`: Count PUSH nodes
- `count_definitions_of_symbol(nodes, symbol)`: Count POP nodes

**Assertions:**
- `assert_node_exists(nodes, symbol, node_type)`: Assert node exists
- `assert_node_has_parent(node, parent_symbol)`: Assert parent relationship
- `assert_node_has_child(node, child_symbol)`: Assert child relationship
- `assert_graph_structure_valid(nodes)`: Validate graph consistency

**Graph Analysis:**
- `get_node_depth(node, roots)`: Calculate node depth
- `get_path_to_node(node, roots)`: Get path from root to node
- `get_scope_chain(node, roots)`: Get scope chain
- `assert_node_in_scope(node, scope_symbol, roots)`: Assert scope membership

### From Base Classes

**Resolution Helpers:**
- `find_push_nodes(roots, symbol)`: Find PUSH nodes
- `find_pop_nodes(roots, symbol)`: Find POP nodes
- `resolve_reference(roots, symbol, index)`: Resolve reference
- `assert_resolution_success(results, symbol)`: Assert successful resolution
- `assert_resolution_failure(results)`: Assert failed resolution
- `assert_all_references_resolve_to_same(roots, symbol)`: Assert consistency

**Graph Helpers:**
- `assert_graph_not_empty(roots, min_nodes)`: Assert graph has nodes
- `assert_node_exists(roots, symbol, type)`: Assert node exists
- `assert_node_count(roots, type, count)`: Assert node count
- `assert_scope_structure(roots, min_scopes)`: Assert scope structure
- `assert_graph_consistency(roots)`: Assert graph consistency

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

### Pattern 4: Edge Cases

```python
def test_undefined_reference(self):
    code = "print(undefined_var)"
    roots = self.build_graph(code)
    push_nodes = self.find_push_nodes(roots, "undefined_var")
    if push_nodes:
        results = self.resolve_reference(roots, "undefined_var")
        self.assert_resolution_failure(results)
```

## Best Practices

### 1. Use Descriptive Names

✅ Good:
```python
def test_resolve_local_variable_shadowing_global():
```

❌ Bad:
```python
def test_1():
```

### 2. Add Docstrings

✅ Good:
```python
def test_resolve_local_variable(self):
    """Test resolving a local variable reference to its definition."""
```

❌ Bad:
```python
def test_resolve_local_variable(self):
    # test
```

### 3. Use Helper Functions

✅ Good:
```python
push_nodes = self.find_push_nodes(roots, "x")
results = self.resolve_reference(roots, "x")
self.assert_resolution_success(results, "x")
```

❌ Bad:
```python
all_nodes = get_all_nodes(roots)
push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
# ... duplicate logic ...
```

### 4. Assert Specific Properties

✅ Good:
```python
assert results[0].definition.type == 'POP'
assert results[0].definition.symbol == 'x'
assert len(results[0].path) > 0
assert results[0].confidence > 0.0
```

❌ Bad:
```python
assert len(results) > 0  # Too vague
```

### 5. Verify Graph Consistency

✅ Good:
```python
def test_complex_structure(self):
    roots = self.build_graph(code)
    # ... test logic ...
    self.assert_graph_consistency(roots)
```

### 6. Test Both Success and Failure

✅ Good:
```python
def test_resolve_defined_variable(self):
    # Test successful resolution
    
def test_resolve_undefined_variable(self):
    # Test failed resolution
```

## Adding Tests for New Languages

1. **Create directory**: `tests/integration/<language>/`
2. **Inherit from base classes**: Use `BaseResolutionTestSuite` and `BaseGraphTestSuite`
3. **Implement `get_language()`**: Return language identifier
4. **Add language-specific tests**: Test unique features
5. **Follow Python patterns**: Use as reference for structure
6. **Document**: Add README explaining language-specific considerations

Example:

```python
from tests.integration.base import BaseResolutionTestSuite

class TestJavaScriptResolution(BaseResolutionTestSuite):
    def get_language(self):
        return "javascript"
    
    def test_resolve_let_variable(self):
        code = "let x = 1;\nconsole.log(x);"
        roots = self.build_graph(code)
        results = self.resolve_reference(roots, "x")
        self.assert_resolution_success(results, "x")
```

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before releases

All tests must pass before code can be merged.

## Performance Testing

Performance tests verify scalability:
- Large graphs (1000+ nodes)
- Deep nesting (100+ levels)
- Many references (100+ to same symbol)
- Complex structures

See `test_resolution_performance.py` for examples.

## Debugging Failed Tests

1. **Run with verbose output**: `pytest -v`
2. **Run specific test**: Isolate the failing test
3. **Add print statements**: Debug intermediate values
4. **Use graph visualization**: See `src/visualizer.py`
5. **Check graph structure**: Use `assert_graph_structure_valid()`

## Future Enhancements

- Multi-file test support
- Regression test suite
- Benchmarking utilities
- Test data fixtures
- Visual debugging helpers
- Property-based testing
