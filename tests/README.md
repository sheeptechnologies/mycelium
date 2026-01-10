# Test Suite Documentation

This directory contains the complete test suite for Mycelium stack graphs library.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and helper functions
├── unit/                    # Unit tests for individual components
│   ├── test_models.py
│   ├── test_graph_builder.py
│   ├── test_captures_manager.py
│   └── test_python_handlers.py
└── integration/             # Integration tests
    ├── base/                # Base classes for multi-language tests
    │   ├── base_resolution_tests.py
    │   ├── base_graph_tests.py
    │   └── README.md
    └── python/              # Python-specific integration tests
        ├── test_resolution_*.py
        ├── test_python_*.py
        └── README.md
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on individual components in isolation:
- **`test_models.py`**: Tests for `GNode` data model
- **`test_graph_builder.py`**: Tests for graph construction logic
- **`test_captures_manager.py`**: Tests for Tree-sitter capture management
- **`test_python_handlers.py`**: Tests for Python-specific handlers

### Integration Tests (`tests/integration/`)

Integration tests verify end-to-end functionality:
- **Base classes** (`base/`): Abstract classes for language-agnostic testing
- **Python tests** (`python/`): Comprehensive tests for Python language support

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Python tests only
pytest tests/integration/python/
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html tests/
```

### Run specific test file
```bash
pytest tests/integration/python/test_resolution_basic.py
```

### Run specific test class or method
```bash
pytest tests/integration/python/test_resolution_basic.py::TestBasicResolution::test_resolve_local_variable
```

## Test Organization Principles

1. **Separation of Concerns**: Unit tests for components, integration tests for workflows
2. **Reusability**: Base classes enable consistent testing across languages
3. **Comprehensiveness**: Tests cover basic cases, edge cases, and performance
4. **Maintainability**: Clear naming, documentation, and consistent patterns

## Adding New Tests

### For Existing Languages

1. Identify the appropriate test file or create a new one
2. Follow existing patterns and naming conventions
3. Use helper functions from `conftest.py` and base classes
4. Add comprehensive assertions (not just existence checks)

### For New Languages

1. Create `tests/integration/<language>/` directory
2. Inherit from base classes in `tests/integration/base/`
3. Follow patterns established in Python tests
4. See `tests/integration/base/README.md` for details

## Helper Functions

See `conftest.py` for available helper functions:
- `find_node_by_symbol()`: Find nodes by symbol
- `count_nodes_by_type()`: Count nodes by type
- `get_all_nodes()`: Get all nodes from graph
- `assert_graph_structure_valid()`: Validate graph consistency
- And more...

## Best Practices

1. **Use descriptive test names**: `test_resolve_local_variable` not `test_1`
2. **Add docstrings**: Explain what each test verifies
3. **Use helper functions**: Don't duplicate graph traversal logic
4. **Assert specific properties**: Not just "node exists" but "node has correct type and symbol"
5. **Test edge cases**: Empty graphs, undefined references, deeply nested structures
6. **Verify graph consistency**: Use `assert_graph_structure_valid()` in complex tests

## Continuous Integration

Tests are run automatically on:
- Every commit to main branch
- Pull requests
- Before releases

All tests must pass before code can be merged.

## Performance Tests

Performance tests verify that resolution and graph building remain efficient:
- Large graphs (many nodes)
- Deeply nested scopes
- Many references to same symbol
- Complex nested structures

See `test_resolution_performance.py` for examples.

## Future Enhancements

- Multi-file test support
- Regression test suite with real-world examples
- Benchmarking utilities
- Test data fixtures for common patterns
- Visual debugging helpers
