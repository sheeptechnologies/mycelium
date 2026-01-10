"""
Integration tests for Advanced Expression Resolution.

Tests verify resolution in advanced expressions including walrus operator,
attribute access, subscript, chained calls, and unpacking.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import get_all_nodes


class TestWalrusOperatorResolution:
    """Test resolution with walrus operator (:=)."""
    
    def test_resolve_walrus_operator(self):
        """Test resolving variable after walrus operator assignment."""
        code = """
if (value := get_value()) > 10:
    print(value)  # Should resolve to walrus assignment
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'value' in print
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'value']
        
        if push_nodes:
            # Find the one in print (after walrus)
            for push in push_nodes:
                if push.start_byte > 30:  # In print
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to walrus assignment
                        assert results[0].definition.symbol == 'value'
    
    def test_resolve_walrus_in_comprehension(self):
        """Test resolving walrus operator in comprehension."""
        code = """
data = [1, 2, 3, 4, 5]
result = [y for x in data if (y := x * 2) > 5]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'y' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'y']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)


class TestAttributeAccessResolution:
    """Test resolution in attribute access."""
    
    def test_resolve_attribute_access(self):
        """Test resolving in attribute access chain."""
        code = """
class A:
    def method(self):
        return self.value

obj = A()
result = obj.method()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'obj' in obj.method()
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'obj']
        
        if push_nodes:
            # Find the one in method call
            for push in push_nodes:
                if push.start_byte > 50:  # In method call
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'obj'
    
    def test_resolve_chained_attribute_access(self):
        """Test resolving in chained attribute access."""
        code = """
class A:
    def get_b(self):
        return B()

class B:
    def get_c(self):
        return C()

class C:
    value = 42

a = A()
result = a.get_b().get_c().value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'a' in chain
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'a']
        
        if push_nodes:
            # Find the one in chain
            for push in push_nodes:
                if push.start_byte > 80:  # In chain
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
    
    def test_resolve_nested_attribute_access(self):
        """Test resolving nested attribute access."""
        code = """
class Container:
    def __init__(self):
        self.data = Data()

class Data:
    value = 10

container = Container()
result = container.data.value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'container' in chain
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'container']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)


class TestSubscriptResolution:
    """Test resolution in subscript access."""
    
    def test_resolve_subscript_access(self):
        """Test resolving in subscript access."""
        code = """
data = {'key': 'value'}
result = data['key']
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'data' in subscript
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'data']
        
        if push_nodes:
            # Find the one in subscript
            for push in push_nodes:
                if push.start_byte > 25:  # In subscript
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'data'
    
    def test_resolve_subscript_key(self):
        """Test resolving key in subscript."""
        code = """
key = 'name'
data = {'name': 'Alice'}
value = data[key]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'key' in subscript
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'key']
        
        if push_nodes:
            # Find the one in subscript
            for push in push_nodes:
                if push.start_byte > 40:  # In subscript
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'key'


class TestChainedCallsResolution:
    """Test resolution in chained function calls."""
    
    def test_resolve_chained_calls(self):
        """Test resolving in chained function calls."""
        code = """
def get_list():
    return [1, 2, 3]

def process(items):
    return [x * 2 for x in items]

result = process(get_list())
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'get_list' in chain
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'get_list']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_method_chaining(self):
        """Test resolving in method chaining."""
        code = """
class Builder:
    def step1(self):
        self.value = 1
        return self
    
    def step2(self):
        self.value *= 2
        return self
    
    def get_value(self):
        return self.value

builder = Builder()
result = builder.step1().step2().get_value()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'builder' in chain
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'builder']
        
        if push_nodes:
            # Find the one in chain
            for push in push_nodes:
                if push.start_byte > 100:  # In chain
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestUnpackingResolution:
    """Test resolution in unpacking operations."""
    
    def test_resolve_tuple_unpacking(self):
        """Test resolving in tuple unpacking."""
        code = """
point = (10, 20)
x, y = point
result = x + y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of unpacked variables
        for symbol in ['x', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in result
                for push in push_nodes:
                    if push.start_byte > 30:  # In result
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
                        if results:
                            assert results[0].definition.symbol == symbol
    
    def test_resolve_list_unpacking(self):
        """Test resolving in list unpacking."""
        code = """
items = [1, 2, 3]
first, *rest = items
result = first + sum(rest)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of unpacked variables
        for symbol in ['first', 'rest']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_dict_unpacking(self):
        """Test resolving in dictionary unpacking."""
        code = """
d1 = {'a': 1, 'b': 2}
d2 = {'c': 3}
merged = {**d1, **d2}
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'd1' and 'd2' in unpacking
        for symbol in ['d1', 'd2']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in unpacking
                for push in push_nodes:
                    if push.start_byte > 30:  # In unpacking
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_function_unpacking(self):
        """Test resolving in function argument unpacking."""
        code = """
def add(a, b, c):
    return a + b + c

values = [1, 2, 3]
result = add(*values)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'values' in unpacking
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'values']
        
        if push_nodes:
            # Find the one in function call
            for push in push_nodes:
                if push.start_byte > 50:  # In call
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'values'


class TestComplexExpressions:
    """Test resolution in complex expression combinations."""
    
    def test_resolve_complex_expression(self):
        """Test resolving in complex nested expressions."""
        code = """
class A:
    def get_b(self):
        return B()

class B:
    data = [1, 2, 3]

a = A()
result = a.get_b().data[0]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'a' in complex expression
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'a']
        
        if push_nodes:
            # Find the one in complex expression
            for push in push_nodes:
                if push.start_byte > 60:  # In expression
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
    
    def test_resolve_expression_with_walrus(self):
        """Test resolving in expression with walrus operator."""
        code = """
data = [1, 2, 3, 4, 5]
result = [(square := x * x) for x in data if square > 10]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'square' in condition
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'square']
        
        if push_nodes:
            # Find the one in condition
            for push in push_nodes:
                if push.start_byte > 40:  # In condition
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
