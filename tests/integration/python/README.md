# Python Integration Tests

Comprehensive integration tests for Python language support in Mycelium stack graphs.

## Overview

These tests verify that the stack graph library correctly:
- Builds stack graphs from Python source code
- Resolves references to their definitions
- Handles Python-specific features (classes, functions, imports, etc.)
- Maintains graph consistency and correctness

## Test Files

### Resolution Tests

#### `test_resolution_basic.py`
Foundation tests for basic resolution scenarios:
- Local variable resolution
- Function parameter resolution
- Multiple references to same symbol
- Basic scoping (shadowing, nested functions)
- Edge cases (undefined references, empty graphs)

#### `test_resolution_functions.py`
Function-related resolution:
- Lambda functions and closures
- Function parameters (defaults, *args, **kwargs)
- Type hints
- Nested functions and closure capture
- Generator and async functions

#### `test_resolution_classes.py`
Class-related resolution:
- Instance methods and `self`
- Class methods and `cls`
- Static methods
- Class attributes
- Inheritance and method resolution
- Properties and descriptors

#### `test_resolution_imports.py`
Import resolution:
- `import` statements
- `from ... import` statements
- Aliased imports
- Relative imports
- Dotted imports
- Wildcard imports

#### `test_resolution_scoping.py`
Advanced scoping scenarios:
- `global` and `nonlocal` statements
- Closure capture at multiple levels
- Scope chain resolution
- Advanced shadowing scenarios
- Scope boundary resolution

#### `test_resolution_control_flow.py`
Control flow constructs:
- `for` loops (loop variables, iterables)
- `while` loops
- `if/elif/else` statements
- `match/case` statements (Python 3.10+)
- `try/except/finally` blocks
- `with` statements

#### `test_resolution_comprehensions.py`
Comprehension resolution:
- List comprehensions
- Dict comprehensions
- Set comprehensions
- Generator expressions
- Nested comprehensions
- Comprehensions with outer scope access

#### `test_resolution_expressions.py`
Complex expression resolution:
- Walrus operator (`:=`)
- Attribute access
- Subscript access
- Chained method calls
- Tuple/list/dict unpacking
- Complex nested expressions

#### `test_resolution_pattern_matching.py`
Pattern matching (Python 3.10+):
- `as` patterns
- Tuple patterns
- List patterns
- Dict patterns
- Class patterns
- Union patterns
- Guards

#### `test_resolution_edge_cases.py`
Edge cases and special scenarios:
- Multiple definitions for same symbol
- Definition priority
- Path correctness and uniqueness
- Performance limits (max_depth, max_paths)
- Error handling
- Confidence calculation

#### `test_resolution_performance.py`
Performance and scalability:
- Large graphs (many nodes)
- Many references to same symbol
- Deeply nested scopes
- Complex nested structures
- Performance regression tests

#### `test_resolution_validation.py`
Algorithm correctness:
- Stack graph rules (symbol stack, scope stack)
- Path finding correctness (BFS, visited tracking)
- Stack management (PUSH, POP, SCOPE)
- Algorithm invariants

### Graph Construction Tests

#### `test_python_complete.py`
Complete examples covering various Python features:
- Classes with inheritance
- Nested functions
- Multiple assignments
- Chained calls
- Lambda functions
- Attribute access
- Return statements
- Complex nested structures
- Imports
- Graph consistency checks

#### `test_python_extended.py`
Extended features and edge cases:
- Import statements (various forms)
- Control flow (if, for, while)
- Exception handling
- Decorators
- Data structures
- Expressions
- Context managers
- Comprehensions
- Advanced features

#### `test_stack_graph_builder.py`
Builder API and file handling:
- Builder initialization
- Building from code strings
- Building from files
- Building from Tree-sitter trees
- Graph structure validation
- Multiple file handling

## Running Python Tests

```bash
# All Python integration tests
pytest tests/integration/python/

# Specific test file
pytest tests/integration/python/test_resolution_basic.py

# Specific test class
pytest tests/integration/python/test_resolution_basic.py::TestBasicResolution

# Specific test method
pytest tests/integration/python/test_resolution_basic.py::TestBasicResolution::test_resolve_local_variable

# With verbose output
pytest -v tests/integration/python/

# With coverage
pytest --cov=src --cov-report=html tests/integration/python/
```

## Test Coverage

The Python test suite covers:

✅ **Basic Features**
- Variables and assignments
- Functions and parameters
- Classes and methods
- Imports

✅ **Advanced Features**
- Closures and nested functions
- Inheritance and polymorphism
- Comprehensions
- Pattern matching (Python 3.10+)
- Async/await
- Generators

✅ **Edge Cases**
- Shadowing and scoping
- Undefined references
- Multiple definitions
- Complex nested structures

✅ **Correctness**
- Graph consistency
- Path correctness
- Algorithm invariants
- Performance limits

## Python-Specific Considerations

### Version Support
- Tests target Python 3.10+ (for pattern matching)
- Some tests may be skipped on older versions

### Tree-sitter Parsing
- Tests rely on tree-sitter-python for parsing
- Some edge cases in parsing may affect test results

### Known Limitations
- Cross-file imports require additional setup
- Some advanced features may have partial support
- Performance tests may vary by system

## Adding New Python Tests

1. **Choose the right file**: Add to existing file if category matches, or create new file
2. **Follow naming conventions**: `test_<feature>_<scenario>`
3. **Use helper functions**: From `conftest.py` and base classes
4. **Add comprehensive assertions**: Verify specific properties, not just existence
5. **Document edge cases**: Add comments explaining Python-specific behavior
6. **Test both success and failure**: Verify correct behavior and error handling

## Example Test

```python
def test_resolve_local_variable(self):
    """Test resolving a local variable reference to its definition."""
    code = """
x = 1
print(x)
"""
    builder = StackGraphBuilder()
    roots = builder.build_from_code(code)
    
    resolver = ReferenceResolver()
    all_nodes = get_all_nodes(roots)
    
    # Find the PUSH node for 'x' in print(x)
    push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
    
    assert len(push_nodes) > 0, "Should find at least one PUSH node for 'x'"
    
    # Resolve the first reference
    results = resolver.resolve(push_nodes[0], roots)
    
    assert len(results) > 0, "Should find at least one definition"
    assert results[0].definition.type == 'POP', "Definition should be a POP node"
    assert results[0].definition.symbol == 'x', "Definition symbol should match"
    assert len(results[0].path) > 0, "Path should not be empty"
    assert results[0].confidence > 0.0, "Confidence should be positive"
```

## Maintenance

- Keep tests up-to-date with Python language evolution
- Update tests when adding new features
- Review and refactor tests periodically
- Ensure all tests pass before merging changes
