"""
Extended integration tests for new Python features.
"""

import pytest

from src.graph_builder import StackGraphBuilder
from tests.conftest import (
    find_node_by_symbol,
    count_nodes_by_type,
    get_all_nodes
)


class TestPythonImports:
    """Test suite for import statements."""
    
    def test_import_statement(self):
        """Test basic import statement."""
        code = "import os"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        import_nodes = [n for n in all_nodes if "import" in n.symbol.lower()]
        assert len(all_nodes) > 0
    
    def test_import_from_statement(self):
        """Test from import statement."""
        code = "from os import path"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
    
    def test_aliased_import(self):
        """Test aliased import."""
        code = "import os as operating_system"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
    
    def test_dotted_import(self):
        """Test dotted name import."""
        code = "import os.path"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonControlFlow:
    """Test suite for control flow statements."""
    
    def test_if_statement(self):
        """Test if statement."""
        code = """
if x > 0:
    return True
else:
    return False
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        if_nodes = [n for n in all_nodes if "if" in n.symbol.lower()]
        assert len(all_nodes) > 0
    
    def test_for_statement(self):
        """Test for loop."""
        code = """
for item in items:
    print(item)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        for_nodes = [n for n in all_nodes if "for" in n.symbol.lower()]
        assert len(all_nodes) > 0
    
    def test_while_statement(self):
        """Test while loop."""
        code = """
while condition:
    do_something()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonExceptions:
    """Test suite for exception handling."""
    
    def test_try_except(self):
        """Test try/except statement."""
        code = """
try:
    risky_operation()
except Exception as e:
    handle_error(e)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        try_nodes = [n for n in all_nodes if "try" in n.symbol.lower() or "except" in n.symbol.lower()]
        assert len(all_nodes) > 0
    
    def test_try_finally(self):
        """Test try/finally statement."""
        code = """
try:
    do_something()
finally:
    cleanup()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonDecorators:
    """Test suite for decorators."""
    
    def test_function_decorator(self):
        """Test function decorator."""
        code = """
@decorator
def my_function():
    pass
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        decorator_nodes = [n for n in all_nodes if "decorator" in n.symbol.lower()]
        assert len(all_nodes) > 0


class TestPythonDataStructures:
    """Test suite for data structures."""
    
    def test_list(self):
        """Test list literal."""
        code = "my_list = [1, 2, 3]"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        list_nodes = [n for n in all_nodes if n.symbol == "list"]
        assert len(all_nodes) > 0
    
    def test_dictionary(self):
        """Test dictionary literal."""
        code = "my_dict = {'key': 'value'}"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        dict_nodes = [n for n in all_nodes if n.symbol == "dictionary"]
        assert len(all_nodes) > 0
    
    def test_tuple(self):
        """Test tuple literal."""
        code = "my_tuple = (1, 2, 3)"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonExpressions:
    """Test suite for expressions."""
    
    def test_subscript(self):
        """Test subscript/indexing."""
        code = "value = my_list[0]"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        subscript_nodes = [n for n in all_nodes if n.symbol == "subscript"]
        assert len(all_nodes) > 0
    
    def test_binary_operator(self):
        """Test binary operators."""
        code = "result = a + b"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
    
    def test_list_splat(self):
        """Test list splat (*args)."""
        code = "func(*args)"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonContextManagers:
    """Test suite for context managers."""
    
    def test_with_statement(self):
        """Test with statement."""
        code = """
with open('file.txt') as f:
    content = f.read()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        with_nodes = [n for n in all_nodes if "with" in n.symbol.lower()]
        assert len(all_nodes) > 0


class TestPythonComprehensions:
    """Test suite for comprehensions."""
    
    def test_list_comprehension(self):
        """Test list comprehension."""
        code = "[x for x in range(10)]"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        comp_nodes = [n for n in all_nodes if "comprehension" in n.symbol.lower()]
        assert len(all_nodes) > 0
    
    def test_dict_comprehension(self):
        """Test dictionary comprehension."""
        code = "{k: v for k, v in items}"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0


class TestPythonAdvanced:
    """Test suite for advanced features."""
    
    def test_named_expression(self):
        """Test walrus operator."""
        code = "if (n := len(items)) > 0:"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
    
    def test_keyword_argument(self):
        """Test keyword arguments."""
        code = "func(keyword=value)"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
    
    def test_default_parameter(self):
        """Test default parameters."""
        code = "def func(param=default): pass"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) > 0
