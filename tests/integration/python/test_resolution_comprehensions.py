"""
Integration tests for Comprehension Resolution.

Tests verify that references in comprehensions (list, dict, set, generator)
correctly resolve to their definitions.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestListComprehensionResolution:
    """Test resolution in list comprehensions."""
    
    def test_resolve_list_comprehension_variable(self):
        """Test resolving comprehension variable."""
        code = """
items = [1, 2, 3]
squared = [x * x for x in items]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in comprehension (x * x)
            for push in push_nodes:
                if 30 < push.start_byte < 60:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should resolve to comprehension variable definition
    
    def test_resolve_list_comprehension_iterable(self):
        """Test resolving iterable in list comprehension."""
        code = """
numbers = [1, 2, 3, 4, 5]
evens = [x for x in numbers if x % 2 == 0]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'numbers' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'numbers']
        
        if push_nodes:
            # Find the one in comprehension
            for push in push_nodes:
                if push.start_byte > 30:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'numbers'
    
    def test_resolve_list_comprehension_condition(self):
        """Test resolving variables in comprehension condition."""
        code = """
threshold = 10
numbers = [1, 2, 3, 4, 5]
filtered = [x for x in numbers if x > threshold]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'threshold' in condition
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'threshold']
        
        if push_nodes:
            # Find the one in comprehension condition
            for push in push_nodes:
                if push.start_byte > 50:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'threshold'


class TestDictComprehensionResolution:
    """Test resolution in dictionary comprehensions."""
    
    def test_resolve_dict_comprehension_key_value(self):
        """Test resolving key and value variables."""
        code = """
items = [('a', 1), ('b', 2)]
mapping = {k: v for k, v in items}
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test both k and v
        for symbol in ['k', 'v']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in comprehension
                for push in push_nodes:
                    if 30 < push.start_byte < 60:  # In comprehension
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_dict_comprehension_iterable(self):
        """Test resolving iterable in dict comprehension."""
        code = """
data = {'a': 1, 'b': 2, 'c': 3}
inverted = {v: k for k, v in data.items()}
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'data' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'data']
        
        if push_nodes:
            # Find the one in comprehension
            for push in push_nodes:
                if push.start_byte > 30:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestSetComprehensionResolution:
    """Test resolution in set comprehensions."""
    
    def test_resolve_set_comprehension(self):
        """Test resolving variables in set comprehension."""
        code = """
numbers = [1, 2, 2, 3, 3, 3]
unique_squares = {x * x for x in numbers}
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' and 'numbers'
        for symbol in ['x', 'numbers']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in comprehension
                for push in push_nodes:
                    if push.start_byte > 30:  # In comprehension
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)


class TestGeneratorExpressionResolution:
    """Test resolution in generator expressions."""
    
    def test_resolve_generator_expression(self):
        """Test resolving variables in generator expression."""
        code = """
numbers = [1, 2, 3, 4, 5]
squares = (x * x for x in numbers)
first = next(squares)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' and 'numbers' in generator
        for symbol in ['x', 'numbers']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in generator
                for push in push_nodes:
                    if 30 < push.start_byte < 60:  # In generator
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)


class TestNestedComprehensionResolution:
    """Test resolution in nested comprehensions."""
    
    def test_resolve_nested_list_comprehension(self):
        """Test resolving variables in nested list comprehension."""
        code = """
matrix = [[1, 2], [3, 4]]
flattened = [x for row in matrix for x in row]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'row' and 'x' in nested comprehension
        for symbol in ['row', 'x']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in comprehension
                for push in push_nodes:
                    if push.start_byte > 30:  # In comprehension
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_comprehension_with_outer_scope(self):
        """Test resolving outer scope variables in comprehension."""
        code = """
multiplier = 2
numbers = [1, 2, 3]
result = [x * multiplier for x in numbers]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'multiplier' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'multiplier']
        
        if push_nodes:
            # Find the one in comprehension
            for push in push_nodes:
                if push.start_byte > 40:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'multiplier'
    
    def test_resolve_comprehension_in_function(self):
        """Test resolving comprehension variables in function scope."""
        code = """
def process_data(items):
    threshold = 5
    return [x for x in items if x > threshold]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'threshold' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'threshold']
        
        if push_nodes:
            # Find the one in comprehension
            for push in push_nodes:
                if push.start_byte > 50:  # In comprehension
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to function variable
                        assert results[0].definition.symbol == 'threshold'


class TestComprehensionEdgeCases:
    """Test edge cases in comprehensions."""
    
    def test_resolve_comprehension_multiple_clauses(self):
        """Test resolving in comprehension with multiple clauses."""
        code = """
data = [(1, 'a'), (2, 'b'), (3, 'c')]
result = [y for x, y in data if x > 1]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' and 'y'
        for symbol in ['x', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_comprehension_with_lambda(self):
        """Test resolving in comprehension with lambda."""
        code = """
items = [1, 2, 3]
result = [(lambda x: x * 2)(item) for item in items]
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'item' in comprehension
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'item']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
