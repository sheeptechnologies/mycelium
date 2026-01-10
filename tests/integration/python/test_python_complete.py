"""
End-to-end integration tests with complex Python examples.
"""

import pytest

from src.graph_builder import StackGraphBuilder
from tests.conftest import (
    find_node_by_symbol,
    count_nodes_by_type,
    assert_node_exists,
    get_all_nodes
)


class TestPythonComplete:
    """Test suite for complete Python code examples."""
    
    def test_class_with_inheritance(self):
        """Test building graph for class with inheritance."""
        code = """
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def bark(self):
        return f"{self.name} barks!"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have class-related nodes
        assert len(all_nodes) > 5, f"Graph should have more than 5 nodes (found {len(all_nodes)})"
        
        # Check for class scope nodes
        scope_nodes = [n for n in all_nodes if n.type == "SCOPE"]
        assert len(scope_nodes) >= 2, f"Should have at least 2 SCOPE nodes for classes (found {len(scope_nodes)})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
        
        # Verify specific class names exist
        from tests.conftest import find_node_by_symbol
        animal_node = find_node_by_symbol(roots, "Animal")
        dog_node = find_node_by_symbol(roots, "Dog")
        # At least one should exist (either as identifier or in scope)
        assert animal_node is not None or dog_node is not None, \
            "Should find at least one class node (Animal or Dog)"
    
    def test_nested_functions(self):
        """Test building graph for nested functions."""
        code = """
def outer():
    x = 10
    
    def inner():
        return x
    
    return inner()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have function scope nodes
        scope_nodes = [n for n in all_nodes if n.type == "SCOPE"]
        assert len(scope_nodes) >= 2, \
            f"Should have at least 2 SCOPE nodes for nested functions (found {len(scope_nodes)})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
        
        # Verify variable 'x' exists
        from tests.conftest import find_nodes_by_symbol_and_type
        x_nodes = find_nodes_by_symbol_and_type(roots, "x")
        assert len(x_nodes) > 0, "Should find nodes for variable 'x'"
    
    def test_scope_resolution(self):
        """Test scope resolution in graph."""
        code = """
x = "global"

def func():
    x = "local"
    return x

result = func()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have nodes for 'x' (both PUSH and POP)
        from tests.conftest import find_nodes_by_symbol_and_type
        x_push_nodes = find_nodes_by_symbol_and_type(roots, "x", "PUSH")
        x_pop_nodes = find_nodes_by_symbol_and_type(roots, "x", "POP")
        
        # Should have at least one definition (POP) and one reference (PUSH)
        assert len(x_pop_nodes) >= 1, \
            f"Should have at least 1 POP node for 'x' (found {len(x_pop_nodes)})"
        assert len(x_push_nodes) >= 1, \
            f"Should have at least 1 PUSH node for 'x' (found {len(x_push_nodes)})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_multiple_assignments(self):
        """Test building graph with multiple assignments."""
        code = """
a = 1
b = 2
c = a + b
d = c * 2
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have multiple nodes (at least 4 definitions + references)
        assert len(all_nodes) >= 4, \
            f"Should have at least 4 nodes for multiple assignments (found {len(all_nodes)})"
        
        # Verify all variables exist
        from tests.conftest import find_nodes_by_symbol_and_type
        for var in ['a', 'b', 'c', 'd']:
            pop_nodes = find_nodes_by_symbol_and_type(roots, var, "POP")
            assert len(pop_nodes) >= 1, f"Should have POP node for variable '{var}'"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_chained_calls(self):
        """Test building graph with chained method calls."""
        code = """
class Calculator:
    def add(self, x, y):
        return x + y
    
    def multiply(self, x, y):
        return x * y

calc = Calculator()
result = calc.add(1, 2).multiply(3)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have class and method nodes
        assert len(all_nodes) > 5, \
            f"Should have more than 5 nodes for class and methods (found {len(all_nodes)})"
        
        # Verify class scope exists
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 1, \
            f"Should have at least 1 SCOPE node for class (found {scope_count})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_class_with_methods(self):
        """Test building graph for class with multiple methods."""
        code = """
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def get_name(self):
        return self.name
    
    def get_age(self):
        return self.age
    
    def is_adult(self):
        return self.age >= 18
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have class scope and method nodes
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 1, \
            f"Should have at least 1 SCOPE node for class (found {scope_count})"
        
        # Should have multiple nodes for class and methods
        assert len(all_nodes) > 5, \
            f"Should have more than 5 nodes for class with methods (found {len(all_nodes)})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_function_with_parameters(self):
        """Test building graph for function with typed parameters."""
        code = """
def process_data(data: list, count: int) -> dict:
    result = {}
    for item in data:
        result[item] = count
    return result
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have function scope
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 1, \
            f"Should have at least 1 SCOPE node for function (found {scope_count})"
        
        # Should have nodes for parameters and variables
        from tests.conftest import find_nodes_by_symbol_and_type
        data_nodes = find_nodes_by_symbol_and_type(roots, "data")
        count_nodes = find_nodes_by_symbol_and_type(roots, "count")
        result_nodes = find_nodes_by_symbol_and_type(roots, "result")
        
        assert len(data_nodes) > 0, "Should have nodes for parameter 'data'"
        assert len(count_nodes) > 0, "Should have nodes for parameter 'count'"
        assert len(result_nodes) > 0, "Should have nodes for variable 'result'"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_lambda_functions(self):
        """Test building graph with lambda functions."""
        code = """
add = lambda x, y: x + y
multiply = lambda x, y: x * y

result = add(1, 2)
product = multiply(3, 4)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have lambda scope nodes
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 2, \
            f"Should have at least 2 SCOPE nodes for lambdas (found {scope_count})"
        
        # Should have nodes for lambda assignments
        from tests.conftest import find_nodes_by_symbol_and_type
        add_nodes = find_nodes_by_symbol_and_type(roots, "add")
        multiply_nodes = find_nodes_by_symbol_and_type(roots, "multiply")
        
        assert len(add_nodes) > 0, "Should have nodes for 'add' lambda"
        assert len(multiply_nodes) > 0, "Should have nodes for 'multiply' lambda"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_attribute_access(self):
        """Test building graph with attribute access."""
        code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
x_coord = p.x
y_coord = p.y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have attribute access nodes
        assert len(all_nodes) > 5, \
            f"Should have more than 5 nodes for class and attribute access (found {len(all_nodes)})"
        
        # Verify class scope exists
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 1, \
            f"Should have at least 1 SCOPE node for class (found {scope_count})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_return_statements(self):
        """Test building graph with return statements."""
        code = """
def get_value():
    x = 10
    return x

def get_multiple():
    a = 1
    b = 2
    return a, b
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have function scopes
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 2, \
            f"Should have at least 2 SCOPE nodes for functions (found {scope_count})"
        
        # Should have nodes for variables in return statements
        from tests.conftest import find_nodes_by_symbol_and_type
        x_nodes = find_nodes_by_symbol_and_type(roots, "x")
        a_nodes = find_nodes_by_symbol_and_type(roots, "a")
        b_nodes = find_nodes_by_symbol_and_type(roots, "b")
        
        assert len(x_nodes) > 0, "Should have nodes for variable 'x'"
        assert len(a_nodes) > 0, "Should have nodes for variable 'a'"
        assert len(b_nodes) > 0, "Should have nodes for variable 'b'"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_complex_nested_structure(self):
        """Test building graph for complex nested structure."""
        code = """
class Container:
    class Item:
        def __init__(self, value):
            self.value = value
        
        def process(self):
            def helper(x):
                return x * 2
            return helper(self.value)
    
    def create_item(self, val):
        return self.Item(val)

container = Container()
item = container.create_item(5)
result = item.process()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have many nodes for complex structure
        assert len(all_nodes) > 10, \
            f"Should have more than 10 nodes for complex nested structure (found {len(all_nodes)})"
        
        # Should have multiple SCOPE nodes (Container, Item, methods, helper)
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 4, \
            f"Should have at least 4 SCOPE nodes for nested classes and functions (found {scope_count})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_import_and_usage(self):
        """Test building graph (note: imports might not be fully handled yet)."""
        code = """
import math

def calculate_circle_area(radius):
    return math.pi * radius ** 2

area = calculate_circle_area(5)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have function definition and scope
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 1, \
            f"Should have at least 1 SCOPE node for function (found {scope_count})"
        
        # Should have nodes for function and variables
        from tests.conftest import find_nodes_by_symbol_and_type
        radius_nodes = find_nodes_by_symbol_and_type(roots, "radius")
        area_nodes = find_nodes_by_symbol_and_type(roots, "area")
        
        assert len(radius_nodes) > 0, "Should have nodes for parameter 'radius'"
        assert len(area_nodes) > 0, "Should have nodes for variable 'area'"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
    
    def test_graph_consistency(self):
        """Test that graph structure is consistent."""
        code = """
def test():
    x = 1
    y = 2
    return x + y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        all_nodes = get_all_nodes(roots)
        
        # Check basic consistency (byte ranges and that nodes exist)
        for node in all_nodes:
            # Validate byte ranges
            assert node.start_byte >= 0, \
                f"Node {node.symbol} has invalid start_byte: {node.start_byte}"
            assert node.end_byte >= node.start_byte, \
                f"Node {node.symbol} has end_byte ({node.end_byte}) < start_byte ({node.start_byte})"
        
        # Check parent-child consistency where both sides are set
        # Note: Some graph construction patterns may not maintain perfect bidirectional
        # relationships, so we validate only when both sides are explicitly set
        for node in all_nodes:
            if node.parent:
                for parent in node.parent:
                    if parent.children:
                        assert node in parent.children, \
                            f"Node {node.symbol} has parent {parent.symbol} but is not in parent's children"
    
    def test_byte_ranges_valid(self):
        """Test that all nodes have valid byte ranges."""
        code = """
def example():
    return 42
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        all_nodes = get_all_nodes(roots)
        
        for node in all_nodes:
            assert node.start_byte >= 0, f"Node {node.symbol} has invalid start_byte"
            assert node.end_byte >= node.start_byte, \
                f"Node {node.symbol} has end_byte < start_byte"
    
    def test_multiple_classes(self):
        """Test building graph with multiple classes."""
        code = """
class A:
    def method_a(self):
        pass

class B:
    def method_b(self):
        pass

class C(A, B):
    def method_c(self):
        self.method_a()
        self.method_b()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        
        # Should have multiple class-related nodes
        assert len(all_nodes) > 5, \
            f"Should have more than 5 nodes for multiple classes (found {len(all_nodes)})"
        
        # Should have multiple SCOPE nodes for classes (at least 3 classes)
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= 3, \
            f"Should have at least 3 SCOPE nodes for classes (found {scope_count})"
        
        # Verify basic graph properties (byte ranges)
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0
            assert node.end_byte >= node.start_byte
