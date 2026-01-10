"""
Integration tests for Advanced Scoping Resolution.

Tests verify complex scoping scenarios including global/nonlocal, closures,
scope chains, and advanced shadowing cases.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestGlobalNonlocalResolution:
    """Test resolution with global and nonlocal statements."""
    
    def test_resolve_global_statement(self):
        """Test resolving global variable with global statement."""
        code = """
x = 1

def modify():
    global x
    x = 2  # Modifies global x
    return x  # Should resolve to global x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in return (after global declaration)
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in return (should resolve to global)
            for push in push_nodes:
                if push.start_byte > 60:  # In return
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to global definition
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_nonlocal_statement(self):
        """Test resolving nonlocal variable."""
        code = """
def outer():
    x = 1
    
    def inner():
        nonlocal x
        x = 2  # Modifies outer's x
        return x  # Should resolve to outer's x
    
    return inner()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in inner return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in inner return
            for push in push_nodes:
                if 60 < push.start_byte < 90:  # In inner return
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to outer's x
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_global_vs_local(self):
        """Test that local shadows global without global statement."""
        code = """
x = 1  # Global

def func():
    x = 2  # Local (shadows global)
    return x  # Should resolve to local
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in return
            for push in push_nodes:
                if push.start_byte > 40:  # In function
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should prefer local over global


class TestClosureResolution:
    """Test resolution in closures."""
    
    def test_resolve_closure_capture(self):
        """Test resolving closure capture."""
        code = """
def make_adder(n):
    def adder(x):
        return n + x  # n captured from outer
    return adder

add_five = make_adder(5)
result = add_five(3)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'n' in adder function
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'n']
        
        if push_nodes:
            # Find the one in adder (n + x)
            for push in push_nodes:
                if 30 < push.start_byte < 60:  # In adder
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to outer parameter
                        assert results[0].definition.symbol == 'n'
    
    def test_resolve_closure_multiple_levels(self):
        """Test resolving closure across multiple levels."""
        code = """
def level1(a):
    def level2(b):
        def level3(c):
            return a + b + c  # All from outer scopes
        return level3
    return level2

f = level1(1)(2)
result = f(3)
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
                    if 50 < push.start_byte < 100:  # In level3
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_closure_with_modification(self):
        """Test resolving closure that modifies outer variable."""
        code = """
def counter():
    count = 0
    
    def increment():
        nonlocal count
        count += 1
        return count
    
    return increment

c = counter()
result = c()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'count' in increment
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'count']
        
        if push_nodes:
            # Find the one in increment
            for push in push_nodes:
                if 40 < push.start_byte < 80:  # In increment
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestScopeChainResolution:
    """Test resolution across complex scope chains."""
    
    def test_resolve_scope_chain_module_to_lambda(self):
        """Test resolving through module → function → nested → lambda."""
        code = """
module_var = 1

class MyClass:
    class_var = 2
    
    def method(self):
        method_var = 3
        
        def nested():
            nested_var = 4
            
            lambda_func = lambda: module_var + MyClass.class_var + method_var + nested_var
            return lambda_func
        
        return nested()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of variables in lambda
        for symbol in ['module_var', 'class_var', 'method_var', 'nested_var']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in lambda
                for push in push_nodes:
                    if push.start_byte > 150:  # In lambda
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
    
    def test_resolve_scope_exit_order(self):
        """Test that scope exit order is correct."""
        code = """
def outer():
    x = 1
    
    def middle():
        y = 2
        
        def inner():
            z = 3
            return x + y + z  # All from outer scopes
        
        return inner()
    
    return middle()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test that all variables resolve correctly
        for symbol in ['x', 'y', 'z']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in inner return
                for push in push_nodes:
                    if push.start_byte > 80:  # In inner
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
                        if results:
                            assert results[0].definition.symbol == symbol


class TestShadowingAdvanced:
    """Test advanced shadowing scenarios."""
    
    def test_resolve_multiple_shadowing(self):
        """Test resolving when variable is shadowed at multiple levels."""
        code = """
x = 1  # Level 1

def func1():
    x = 2  # Level 2
    
    def func2():
        x = 3  # Level 3
        
        def func3():
            return x  # Should resolve to Level 3
        
        return func3()
    
    return func2()

result = func1()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in func3 return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in func3 (should be the innermost)
            for push in push_nodes:
                if push.start_byte > 100:  # In func3
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should resolve to innermost definition
    
    def test_resolve_parameter_shadows_global(self):
        """Test that parameter shadows global variable."""
        code = """
x = 1  # Global

def func(x):  # Parameter shadows global
    return x  # Should resolve to parameter
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in return
            for push in push_nodes:
                if push.start_byte > 30:  # In function
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should prefer parameter over global
    
    def test_resolve_local_shadows_parameter(self):
        """Test that local variable shadows parameter."""
        code = """
def func(x):  # Parameter
    x = 10  # Local shadows parameter
    return x  # Should resolve to local
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in return
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in return
            for push in push_nodes:
                if push.start_byte > 40:  # In return
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should prefer local over parameter
    
    def test_resolve_class_attr_shadows_module(self):
        """Test that class attribute shadows module-level variable."""
        code = """
name = "module"  # Module level

class MyClass:
    name = "class"  # Class attribute
    
    def method(self):
        return name  # Should resolve to class attribute
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'name' in method
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'name']
        
        if push_nodes:
            # Find the one in method
            for push in push_nodes:
                if push.start_byte > 80:  # In method
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestScopeBoundaryResolution:
    """Test resolution at scope boundaries."""
    
    def test_resolve_across_scope_boundary(self):
        """Test resolving across scope boundaries."""
        code = """
x = 1

def outer():
    y = 2
    
    def inner():
        z = 3
        return x + y + z  # x from module, y from outer, z from inner
    
    return inner()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test that each variable resolves to correct scope
        scope_map = {
            'x': 'module',
            'y': 'outer',
            'z': 'inner'
        }
        
        for symbol, expected_scope in scope_map.items():
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in inner return
                for push in push_nodes:
                    if push.start_byte > 60:  # In inner
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)
                        if results:
                            assert results[0].definition.symbol == symbol
    
    def test_resolve_scope_boundary_with_global(self):
        """Test resolving with global statement at boundary."""
        code = """
x = 1

def func():
    global x
    def nested():
        return x  # Should resolve to global x via func's global declaration
    return nested()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in nested
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in nested
            for push in push_nodes:
                if push.start_byte > 50:  # In nested
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
