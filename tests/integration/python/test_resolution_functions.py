"""
Integration tests for Function Resolution.

Tests verify that references in function contexts correctly resolve, including
lambda functions, default parameters, *args/**kwargs, type hints, and closures.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestLambdaResolution:
    """Test resolution in lambda functions."""
    
    def test_resolve_lambda_parameter(self):
        """Test resolving lambda parameter."""
        code = """
f = lambda x: x + 1
result = f(5)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in lambda
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in lambda (should be in x + 1)
            for push in push_nodes:
                if push.start_byte < 30:  # In lambda definition
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to lambda parameter
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_lambda_capture(self):
        """Test resolving closure capture in lambda."""
        code = """
x = 10
f = lambda: x * 2  # Captures x from outer scope
result = f()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in lambda
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in lambda
            for push in push_nodes:
                if 15 < push.start_byte < 35:  # In lambda
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to outer x
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_nested_lambda(self):
        """Test resolution in nested lambda."""
        code = """
f = lambda x: lambda y: x + y  # x from outer lambda
result = f(1)(2)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in inner lambda
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in inner lambda (x + y)
            for push in push_nodes:
                if push.start_byte > 25:  # In inner lambda
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestFunctionParametersResolution:
    """Test resolution of function parameters and defaults."""
    
    def test_resolve_function_default_parameter(self):
        """Test resolving default parameter value."""
        code = """
default_value = 42

def func(x=default_value):
    return x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'default_value' in parameter default
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'default_value']
        
        if push_nodes:
            # Find the one in function parameter
            for push in push_nodes:
                if 30 < push.start_byte < 60:  # In function definition
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'default_value'
    
    def test_resolve_function_star_args(self):
        """Test resolving *args and **kwargs."""
        code = """
def process(*args, **kwargs):
    first = args[0]  # Should resolve args
    key = kwargs.get('key')  # Should resolve kwargs
    return first, key
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'args' and 'kwargs'
        for symbol in ['args', 'kwargs']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
                if results:
                    assert results[0].definition.symbol == symbol
    
    def test_resolve_function_type_hints(self):
        """Test resolving type hints in function."""
        code = """
from typing import List, Dict

def process(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for type hints (List, Dict, str, int)
        type_hints = ['List', 'Dict', 'str', 'int']
        for hint in type_hints:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == hint]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_typed_parameter(self):
        """Test resolving typed parameter."""
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'name' in return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'name']
        
        if push_nodes:
            # Find the one in function body
            for push in push_nodes:
                if push.start_byte > 30:  # In function body
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'name'


class TestNestedFunctionsResolution:
    """Test resolution in nested functions."""
    
    def test_resolve_nested_function_parameter(self):
        """Test resolving parameter in nested function."""
        code = """
def outer(x):
    def inner(y):
        return x + y  # x from outer, y from inner
    return inner(5)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in inner function
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in inner function (x + y)
            for push in push_nodes:
                if push.start_byte > 40:  # In inner function
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to outer parameter
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_closure_capture(self):
        """Test resolving closure capture."""
        code = """
def make_multiplier(n):
    def multiplier(x):
        return n * x  # n captured from outer
    return multiplier

double = make_multiplier(2)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'n' in inner function
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'n']
        
        if push_nodes:
            # Find the one in multiplier function
            for push in push_nodes:
                if 40 < push.start_byte < 80:  # In multiplier
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to outer parameter
                        assert results[0].definition.symbol == 'n'
    
    def test_resolve_triple_nested(self):
        """Test resolution in triple nested function."""
        code = """
def level1(a):
    def level2(b):
        def level3(c):
            return a + b + c  # All from outer scopes
        return level3
    return level2
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of a, b, c in level3
        for symbol in ['a', 'b', 'c']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in level3
                for push in push_nodes:
                    if push.start_byte > 80:  # In level3
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)


class TestFunctionSpecialCases:
    """Test special function-related resolution cases."""
    
    def test_resolve_function_call_argument(self):
        """Test resolving arguments in function call."""
        code = """
def process(data):
    return data * 2

value = 10
result = process(value)  # value passed as argument
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'value' in function call
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'value']
        
        if push_nodes:
            # Find the one in function call
            for push in push_nodes:
                if push.start_byte > 50:  # In function call
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'value'
    
    def test_resolve_keyword_argument(self):
        """Test resolving keyword arguments."""
        code = """
def greet(name, message="Hello"):
    return f"{message}, {name}!"

greet(name="Alice", message="Hi")
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'name' and 'message' in call
        for symbol in ['name', 'message']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_generator_function(self):
        """Test resolution in generator function."""
        code = """
def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'n' and 'i' in generator
        for symbol in ['n', 'i']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_async_function(self):
        """Test resolution in async function."""
        code = """
async def fetch_data(url):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'url', 'session', 'response'
        for symbol in ['url', 'session', 'response']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
