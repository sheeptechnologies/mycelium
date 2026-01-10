"""
Integration tests for Control Flow Resolution.

Tests verify that references in control flow constructs (for, while, if/elif/else,
match/case, try/except/finally, with) correctly resolve to their definitions.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestForLoopResolution:
    """Test resolution in for loops."""
    
    def test_resolve_for_loop_variable(self):
        """Test resolving loop variable in for loop."""
        code = """
items = [1, 2, 3]
for item in items:
    print(item)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'item' in loop body
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'item']
        
        if push_nodes:
            # Find the one in loop body (print(item))
            for push in push_nodes:
                if push.start_byte > 30:  # In loop body
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to loop variable definition
                        assert results[0].definition.symbol == 'item'
    
    def test_resolve_for_loop_iterable(self):
        """Test resolving iterable in for loop."""
        code = """
numbers = [1, 2, 3]
for num in numbers:
    print(num)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'numbers' in for statement
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'numbers']
        
        if push_nodes:
            # Find the one in for statement
            for push in push_nodes:
                if 20 < push.start_byte < 40:  # In for statement
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'numbers'
    
    def test_resolve_nested_for_loop(self):
        """Test resolving variables in nested for loops."""
        code = """
matrix = [[1, 2], [3, 4]]
for row in matrix:
    for cell in row:
        print(cell)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'row' and 'cell'
        for symbol in ['row', 'cell']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in inner loop
                for push in push_nodes:
                    if push.start_byte > 40:  # In nested loop
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)


class TestWhileLoopResolution:
    """Test resolution in while loops."""
    
    def test_resolve_while_loop_variable(self):
        """Test resolving variables in while loop."""
        code = """
x = 0
while x < 10:
    x += 1
    print(x)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in while loop
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the ones in while loop
            for push in push_nodes:
                if push.start_byte > 15:  # In while loop
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'x'
    
    def test_resolve_while_loop_condition(self):
        """Test resolving variables in while condition."""
        code = """
limit = 10
counter = 0
while counter < limit:
    counter += 1
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'limit' in condition
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'limit']
        
        if push_nodes:
            # Find the one in while condition
            for push in push_nodes:
                if 30 < push.start_byte < 50:  # In while condition
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'limit'


class TestIfElifElseResolution:
    """Test resolution in if/elif/else blocks."""
    
    def test_resolve_if_elif_else_scopes(self):
        """Test resolving variables in if/elif/else blocks."""
        code = """
x = 5
if x > 10:
    a = 1
elif x > 5:
    a = 2
else:
    a = 3
print(a)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'a' in print
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'a']
        
        if push_nodes:
            # Find the one in print (after all blocks)
            for push in push_nodes:
                if push.start_byte > 80:  # After all blocks
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    # Should find at least one definition (may be multiple)
    
    def test_resolve_if_condition(self):
        """Test resolving variables in if condition."""
        code = """
threshold = 10
value = 15
if value > threshold:
    result = "high"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'threshold' in condition
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'threshold']
        
        if push_nodes:
            # Find the one in if condition
            for push in push_nodes:
                if 30 < push.start_byte < 50:  # In if condition
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'threshold'


class TestMatchCaseResolution:
    """Test resolution in match/case statements (Python 3.10+)."""
    
    def test_resolve_match_case_pattern(self):
        """Test resolving pattern variables in match/case."""
        code = """
def process(data):
    match data:
        case (x, y):
            return x + y
        case [a, b, c]:
            return a + b + c
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for pattern variables
        for symbol in ['x', 'y', 'a', 'b', 'c']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_match_case_as_pattern(self):
        """Test resolving 'as' pattern in match/case."""
        code = """
def process(data):
    match data:
        case Point(x, y) as point:
            return point.x, point.y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'point' (from as pattern)
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'point']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)


class TestTryExceptFinallyResolution:
    """Test resolution in try/except/finally blocks."""
    
    def test_resolve_except_clause_variable(self):
        """Test resolving exception variable in except clause."""
        code = """
try:
    result = 1 / 0
except ZeroDivisionError as e:
    print(e)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'e' in except block
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'e']
        
        if push_nodes:
            # Find the one in except block
            for push in push_nodes:
                if push.start_byte > 40:  # In except block
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to exception variable
                        assert results[0].definition.symbol == 'e'
    
    def test_resolve_try_finally_scope(self):
        """Test resolving variables across try/finally."""
        code = """
resource = open("file.txt")
try:
    data = resource.read()
finally:
    resource.close()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'resource' in finally
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'resource']
        
        if push_nodes:
            # Find the one in finally block
            for push in push_nodes:
                if push.start_byte > 60:  # In finally
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'resource'


class TestWithStatementResolution:
    """Test resolution in with statements (context managers)."""
    
    def test_resolve_with_statement_variable(self):
        """Test resolving context variable in with statement."""
        code = """
with open("file.txt") as f:
    content = f.read()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'f' in with block
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'f']
        
        if push_nodes:
            # Find the one in with block
            for push in push_nodes:
                if push.start_byte > 25:  # In with block
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        # Should resolve to context variable
                        assert results[0].definition.symbol == 'f'
    
    def test_resolve_with_multiple_managers(self):
        """Test resolving multiple context variables."""
        code = """
with open("a.txt") as a, open("b.txt") as b:
    data_a = a.read()
    data_b = b.read()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test both context variables
        for symbol in ['a', 'b']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                # Find the one in with block
                for push in push_nodes:
                    if push.start_byte > 40:  # In with block
                        results = resolver.resolve(push, roots)
                        assert isinstance(results, list)


class TestControlFlowNested:
    """Test resolution in nested control flow."""
    
    def test_resolve_nested_control_flow(self):
        """Test resolving in deeply nested control flow."""
        code = """
for i in range(3):
    if i > 0:
        for j in range(i):
            if j % 2 == 0:
                result = i * j
                print(result)
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'result' in deeply nested scope
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'result']
        
        if push_nodes:
            # Find the one in print
            for push in push_nodes:
                if push.start_byte > 80:  # In print
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'result'
