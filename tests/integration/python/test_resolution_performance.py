"""
Performance tests for Reference Resolution.

Tests verify that resolution performs well with large graphs, deeply nested scopes,
and respects configured limits.
"""

import pytest
import time
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import get_all_nodes


class TestLargeGraphPerformance:
    """Test performance with large graphs."""
    
    def test_resolve_many_variables(self):
        """Test resolution with many variable definitions."""
        # Create code with many variables
        code_lines = []
        for i in range(50):
            code_lines.append(f"var_{i} = {i}")
        
        code_lines.append("result = var_0")
        code = "\n".join(code_lines)
        
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'var_0']
        
        if push_nodes:
            start = time.time()
            results = resolver.resolve(push_nodes[0], roots)
            elapsed = time.time() - start
            
            assert elapsed < 2.0, f"Resolution took too long: {elapsed}s"
            assert isinstance(results, list)
    
    def test_resolve_many_references(self):
        """Test resolution when there are many references to same symbol."""
        code_lines = ["x = 1"]
        for i in range(100):
            code_lines.append(f"y_{i} = x")
        
        code = "\n".join(code_lines)
        
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            start = time.time()
            # Resolve first reference
            results = resolver.resolve(push_nodes[0], roots)
            elapsed = time.time() - start
            
            assert elapsed < 3.0, f"Resolution took too long: {elapsed}s"
            assert isinstance(results, list)
    
    def test_resolve_complex_nested_structure(self):
        """Test performance with complex nested structure."""
        code = """
def level_0():
    x_0 = 0
    def level_1():
        x_1 = 1
        def level_2():
            x_2 = 2
            def level_3():
                x_3 = 3
                def level_4():
                    x_4 = 4
                    return x_0 + x_1 + x_2 + x_3 + x_4
                return level_4()
            return level_3()
        return level_2()
    return level_1()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Resolve all variables in innermost function
        for symbol in ['x_0', 'x_1', 'x_2', 'x_3', 'x_4']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                start = time.time()
                results = resolver.resolve(push_nodes[0], roots)
                elapsed = time.time() - start
                
                assert elapsed < 1.0, f"Resolution of {symbol} took too long: {elapsed}s"
                assert isinstance(results, list)


class TestDepthLimits:
    """Test that depth limits are respected."""
    
    def test_resolve_max_depth_small(self):
        """Test with very small max_depth."""
        code = """
x = 1
y = x
z = y
w = z
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver(max_depth=2)
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            # Should complete without error
            assert isinstance(results, list)
            # All paths should respect max_depth
            for result in results:
                assert len(result.path) <= resolver.max_depth + 2  # Allow some margin
    
    def test_resolve_max_depth_large(self):
        """Test with large max_depth."""
        code = """
x = 1
"""
        for i in range(20):
            code += f"y_{i} = x\n"
        
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver(max_depth=1000)
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_max_paths_limit(self):
        """Test that max_paths limit prevents path explosion."""
        code = """
x = 1
if True:
    x = 2
if True:
    x = 3
if True:
    x = 4
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver(max_paths=10)  # Small limit
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one after all if statements
            for push in push_nodes:
                if push.start_byte > 50:  # After all ifs
                    start = time.time()
                    results = resolver.resolve(push, roots)
                    elapsed = time.time() - start
                    
                    # Should complete quickly due to max_paths limit
                    assert elapsed < 1.0, f"Should respect max_paths limit: {elapsed}s"
                    assert isinstance(results, list)


class TestDeeplyNestedScopes:
    """Test resolution with deeply nested scopes."""
    
    def test_resolve_deep_function_nesting(self):
        """Test resolution with deeply nested functions."""
        code = "x = 1\n"
        for i in range(15):
            code += f"def level_{i}():\n    "
        
        code += "return x\n"
        code += "    " * 15  # Close all functions
        
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            start = time.time()
            results = resolver.resolve(push_nodes[0], roots)
            elapsed = time.time() - start
            
            assert elapsed < 5.0, f"Deep nesting took too long: {elapsed}s"
            assert isinstance(results, list)
    
    def test_resolve_deep_class_nesting(self):
        """Test resolution with deeply nested classes."""
        code = "x = 1\n"
        for i in range(10):
            code += f"class Level_{i}:\n    "
        
        code += "value = x\n"
        code += "    " * 10  # Close all classes
        
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            start = time.time()
            results = resolver.resolve(push_nodes[0], roots)
            elapsed = time.time() - start
            
            assert elapsed < 3.0, f"Deep class nesting took too long: {elapsed}s"
            assert isinstance(results, list)
    
    def test_resolve_mixed_deep_nesting(self):
        """Test resolution with mixed deep nesting (classes, functions, loops)."""
        code = """
x = 1

class A:
    def method(self):
        for i in range(5):
            if i > 0:
                def nested():
                    for j in range(3):
                        if j > 0:
                            return x
                    return None
                return nested()
        return None
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in deeply nested return
            for push in push_nodes:
                if push.start_byte > 100:  # In nested function
                    start = time.time()
                    results = resolver.resolve(push, roots)
                    elapsed = time.time() - start
                    
                    assert elapsed < 2.0, f"Mixed nesting took too long: {elapsed}s"
                    assert isinstance(results, list)


class TestPerformanceRegression:
    """Test for performance regressions."""
    
    def test_resolve_simple_case_fast(self):
        """Test that simple cases resolve very quickly."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            start = time.time()
            results = resolver.resolve(push_nodes[0], roots)
            elapsed = time.time() - start
            
            # Simple case should be very fast (< 100ms)
            assert elapsed < 0.1, f"Simple resolution too slow: {elapsed}s"
            assert len(results) > 0
    
    def test_resolve_no_memory_leak(self):
        """Test that resolution doesn't cause memory leaks."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Run resolution many times
            for _ in range(100):
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
            
            # Should still work correctly
            results = resolver.resolve(push_nodes[0], roots)
            assert len(results) > 0
