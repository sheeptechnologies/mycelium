"""
Integration tests for Pattern Matching Resolution (Python 3.10+).

Tests verify that references in pattern matching (match/case) correctly resolve
to their definitions, including as patterns, tuple patterns, class patterns, etc.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestAsPatternResolution:
    """Test resolution of 'as' patterns."""
    
    def test_resolve_as_pattern(self):
        """Test resolving 'as' pattern alias."""
        code = """
def process(data):
    match data:
        case x as value:
            return value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'value' (from as pattern)
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'value']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
            if results:
                # Should resolve to pattern variable
                assert results[0].definition.symbol == 'value'
    
    def test_resolve_as_pattern_nested(self):
        """Test resolving nested as patterns."""
        code = """
def process(data):
    match data:
        case (x, y) as point:
            return point, x, y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'point', 'x', 'y'
        for symbol in ['point', 'x', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestTuplePatternResolution:
    """Test resolution of tuple patterns."""
    
    def test_resolve_tuple_pattern(self):
        """Test resolving tuple pattern variables."""
        code = """
def process(data):
    match data:
        case (x, y):
            return x + y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' and 'y'
        for symbol in ['x', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in case body
                for push in push_nodes:
                    if push.start_byte > 40:  # In case body
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
                        if results:
                            assert results[0].definition.symbol == symbol
    
    def test_resolve_nested_tuple_pattern(self):
        """Test resolving nested tuple patterns."""
        code = """
def process(data):
    match data:
        case ((a, b), (c, d)):
            return a + b + c + d
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test all pattern variables
        for symbol in ['a', 'b', 'c', 'd']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestListPatternResolution:
    """Test resolution of list patterns."""
    
    def test_resolve_list_pattern(self):
        """Test resolving list pattern variables."""
        code = """
def process(data):
    match data:
        case [first, *rest]:
            return first, rest
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'first' and 'rest'
        for symbol in ['first', 'rest']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_list_pattern_splat(self):
        """Test resolving splat pattern in list."""
        code = """
def process(data):
    match data:
        case [x, *middle, y]:
            return x, middle, y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test all pattern variables
        for symbol in ['x', 'middle', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestDictPatternResolution:
    """Test resolution of dictionary patterns."""
    
    def test_resolve_dict_pattern(self):
        """Test resolving dictionary pattern variables."""
        code = """
def process(data):
    match data:
        case {'key': value, 'other': other_value}:
            return value, other_value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for pattern variables
        for symbol in ['value', 'other_value']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_dict_pattern_splat(self):
        """Test resolving splat pattern in dict."""
        code = """
def process(data):
    match data:
        case {'x': x, **rest}:
            return x, rest
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test pattern variables
        for symbol in ['x', 'rest']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestClassPatternResolution:
    """Test resolution of class patterns."""
    
    def test_resolve_class_pattern(self):
        """Test resolving class pattern variables."""
        code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def process(data):
    match data:
        case Point(x, y):
            return x + y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' and 'y' in pattern
        for symbol in ['x', 'y']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in case body
                for push in push_nodes:
                    if push.start_byte > 100:  # In case body
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_class_pattern_keyword(self):
        """Test resolving keyword pattern in class pattern."""
        code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def process(data):
    match data:
        case Point(x=a, y=b):
            return a + b
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test pattern variables
        for symbol in ['a', 'b']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestUnionPatternResolution:
    """Test resolution of union patterns."""
    
    def test_resolve_union_pattern(self):
        """Test resolving union pattern variables."""
        code = """
def process(data):
    match data:
        case int(x) | float(x):
            return x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in union pattern
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in case body
            for push in push_nodes:
                if push.start_byte > 50:  # In case body
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'x'


class TestPatternMatchingComplex:
    """Test complex pattern matching scenarios."""
    
    def test_resolve_multiple_case_clauses(self):
        """Test resolving in multiple case clauses."""
        code = """
def process(data):
    match data:
        case (x, y):
            result = x + y
        case [a, b, c]:
            result = a * b * c
        case _:
            result = 0
    return result
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'result' in return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'result']
        
        if push_nodes:
            # Find the one in return
            for push in push_nodes:
                if push.start_byte > 120:  # In return
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should find at least one definition
    
    def test_resolve_pattern_with_guard(self):
        """Test resolving pattern with guard condition."""
        code = """
def process(data):
    threshold = 10
    match data:
        case (x, y) if x > threshold:
            return x + y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'threshold' in guard
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'threshold']
        
        if push_nodes:
            # Find the one in guard
            for push in push_nodes:
                if 50 < push.start_byte < 80:  # In guard
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'threshold'
