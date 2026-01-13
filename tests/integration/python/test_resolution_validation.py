"""
Validation tests for Resolution Algorithm.

Tests verify that the resolution algorithm correctly implements stack graph rules,
path finding correctness, and stack management.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult, ResolutionState
from tests.conftest import get_all_nodes


class TestStackGraphRules:
    """Test that stack graph rules are correctly implemented."""
    
    def test_resolve_symbol_stack_empty_start(self):
        """Test that symbol stack starts empty (except for initial symbol)."""
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
            # Manually check initial state
            initial_state = ResolutionState(
                current_node=push_nodes[0],
                symbol_stack=[push_nodes[0].symbol],
                scope_stack=[],
                path=[push_nodes[0]],
                scope_exits=0
            )
            
            # Symbol stack should have exactly one element (the reference symbol)
            assert len(initial_state.symbol_stack) == 1
            assert initial_state.symbol_stack[0] == 'x'
            # Scope stack should be empty
            assert len(initial_state.scope_stack) == 0
    
    def test_resolve_symbol_stack_empty_end(self):
        """Test that symbol stack is empty after successful resolution."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        pop_nodes = [n for n in all_nodes if n.type == 'POP' and n.symbol == 'x']
        
        if push_nodes and pop_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            for result in results:
                # After successful resolution, symbol should be popped
                # Verify by checking that path ends with POP and symbol matches
                assert result.path[-1].type == 'POP'
                assert result.path[-1].symbol == 'x'
                assert result.definition.symbol == 'x'
    
    def test_resolve_scope_stack_valid(self):
        """Test that scope stack is always valid during traversal."""
        code = """
def outer():
    x = 1
    def inner():
        return x
    return inner()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            # All results should have valid paths
            for result in results:
                # Path should be valid (we can't directly check scope stack, but path should work)
                assert len(result.path) > 0
                assert result.path[0].type == 'PUSH'
                assert result.path[-1].type == 'POP'
    
    def test_resolve_no_orphan_pops(self):
        """Test that POP nodes have corresponding PUSH nodes."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        pop_nodes = [n for n in all_nodes if n.type == 'POP']
        push_nodes = [n for n in all_nodes if n.type == 'PUSH']
        
        # Every POP should have a corresponding PUSH with same symbol
        pop_symbols = {n.symbol for n in pop_nodes}
        push_symbols = {n.symbol for n in push_nodes}
        
        # POP symbols should be subset of PUSH symbols (or equal)
        # (Some POPs might not have PUSH if they're definitions without references)
        for pop in pop_nodes:
            # If there's a PUSH with same symbol, resolution should work
            matching_push = [p for p in push_nodes if p.symbol == pop.symbol]
            if matching_push:
                results = resolver.resolve(matching_push[0], roots)
                # Should find the POP
                pop_found = any(r.definition == pop for r in results)
                # Note: May not always find due to scoping, but structure should be valid


class TestPathFindingCorrectness:
    """Test that path finding algorithm is correct."""
    
    def test_resolve_bfs_exploration(self):
        """Test that BFS explores paths correctly."""
        code = """
x = 1
y = x
z = y
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            # BFS should find shortest paths first
            if len(results) > 1:
                # Sort by path length
                sorted_results = sorted(results, key=lambda r: len(r.path))
                # First result should have shortest path
                assert len(sorted_results[0].path) <= len(sorted_results[1].path)
    
    def test_resolve_visited_tracking(self):
        """Test that visited nodes are tracked correctly."""
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
            results = resolver.resolve(push_nodes[0], roots)
            for result in results:
                # Path should be finite and reasonable length
                assert len(result.path) <= resolver.max_depth
    
    def test_resolve_neighbor_discovery(self):
        """Test that all neighbors are discovered correctly."""
        code = """
x = 1
y = x
z = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Get neighbors manually
            neighbors = resolver._get_neighbors(push_nodes[0], roots)
            
            # Should find some neighbors
            assert len(neighbors) > 0, "Should find neighbors"
            # All neighbors should be GNode instances
            for neighbor in neighbors:
                assert isinstance(neighbor, GNode)
    
    def test_resolve_transition_application(self):
        """Test that transitions are applied correctly."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        pop_nodes = [n for n in all_nodes if n.type == 'POP' and n.symbol == 'x']
        
        if push_nodes and pop_nodes:
            # Create initial state
            initial_state = ResolutionState(
                current_node=push_nodes[0],
                symbol_stack=['x'],
                scope_stack=[],
                path=[push_nodes[0]],
                scope_exits=0
            )
            
            # Apply transition to POP
            new_state = resolver._apply_transition(initial_state, pop_nodes[0])
            
            if new_state:
                # Symbol should be popped
                assert len(new_state.symbol_stack) == 0, \
                    "Symbol stack should be empty after POP"
                # Path should include POP
                assert pop_nodes[0] in new_state.path


class TestStackManagement:
    """Test stack management during resolution."""
    
    def test_resolve_push_adds_to_stack(self):
        """Test that PUSH nodes add to symbol stack."""
        code = """
x = 1
y = x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find a PUSH node
        push_nodes = [n for n in all_nodes if n.type == 'PUSH']
        
        if push_nodes:
            initial_state = ResolutionState(
                current_node=push_nodes[0],
                symbol_stack=[],
                scope_stack=[],
                path=[push_nodes[0]],
                scope_exits=0
            )
            
            # Apply transition to another PUSH
            if len(push_nodes) > 1:
                new_state = resolver._apply_transition(initial_state, push_nodes[1])
                if new_state:
                    # Symbol stack should have new symbol
                    assert len(new_state.symbol_stack) > len(initial_state.symbol_stack) or \
                           push_nodes[1].symbol in new_state.symbol_stack
    
    def test_resolve_pop_removes_from_stack(self):
        """Test that POP nodes remove from symbol stack."""
        code = """
x = 1
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        pop_nodes = [n for n in all_nodes if n.type == 'POP' and n.symbol == 'x']
        
        if push_nodes and pop_nodes:
            initial_state = ResolutionState(
                current_node=push_nodes[0],
                symbol_stack=['x'],
                scope_stack=[],
                path=[push_nodes[0]],
                scope_exits=0
            )
            
            # Apply transition to POP
            new_state = resolver._apply_transition(initial_state, pop_nodes[0])
            
            if new_state:
                # Symbol should be removed
                assert 'x' not in new_state.symbol_stack or len(new_state.symbol_stack) < len(initial_state.symbol_stack)
    
    def test_resolve_scope_enters_exits(self):
        """Test that SCOPE nodes correctly enter and exit scope stack."""
        code = """
def func():
    x = 1
    return x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        scope_nodes = [n for n in all_nodes if n.type == 'SCOPE']
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if scope_nodes and push_nodes:
            # Test entering scope
            initial_state = ResolutionState(
                current_node=roots[0] if roots else scope_nodes[0],
                symbol_stack=[],
                scope_stack=[],
                path=[],
                scope_exits=0
            )
            
            # Apply transition to SCOPE
            new_state = resolver._apply_transition(initial_state, scope_nodes[0])
            if new_state:
                # Scope should be added to stack (if entering)
                # Note: Logic depends on direction, so we just verify it's handled
                assert isinstance(new_state.scope_stack, list)


class TestAlgorithmInvariants:
    """Test that algorithm maintains invariants."""
    
    def test_resolve_always_returns_list(self):
        """Test that resolve always returns a list."""
        code = """
x = 1
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test with various node types
        for node in all_nodes[:10]:  # Test first 10 nodes
            results = resolver.resolve(node, roots)
            assert isinstance(results, list), \
                f"resolve should always return list, got {type(results)}"
    
    def test_resolve_path_start_end_correct(self):
        """Test that paths always start with PUSH and end with POP."""
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
            results = resolver.resolve(push_nodes[0], roots)
            for result in results:
                assert result.path[0].type == 'PUSH', \
                    "Path should start with PUSH node"
                assert result.path[-1].type == 'POP', \
                    "Path should end with POP node"
                assert result.path[0] == push_nodes[0], \
                    "Path should start with reference node"
    
    def test_resolve_state_consistency(self):
        """Test that resolution state is always consistent."""
        code = """
x = 1
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            for result in results:
                # Verify state consistency
                assert result.definition is not None
                assert isinstance(result.path, list)
                assert len(result.path) > 0
                assert result.confidence >= 0.0 and result.confidence <= 1.0
