"""
Reference Resolution Facade for Stack Graphs.

This module implements the stack graph resolution algorithm to find definitions (POP)
starting from references (PUSH) using symbol stack and scope stack.
"""

import logging
from typing import List, Set, Optional
from collections import deque

from .models import GNode, ResolutionResult, ResolutionState

logger = logging.getLogger(__name__)


class ReferenceResolver:
    """
    Facade for resolving references to definitions using stack graph algorithm.
    
    The resolution algorithm uses two stacks:
    - Symbol Stack: tracks symbols we're trying to resolve
    - Scope Stack: tracks active scopes during traversal
    
    A valid resolution path must:
    1. Start with a PUSH node (reference)
    2. End with a POP node (definition) with matching symbol
    3. Have both stacks empty at the start and end of the path
    """
    
    def __init__(self, max_depth: int = 1000, max_paths: int = 100):
        """
        Initialize the resolver.
        
        Args:
            max_depth: Maximum depth for path traversal (prevents infinite loops)
            max_paths: Maximum number of paths to explore (prevents explosion)
        """
        self.max_depth = max_depth
        self.max_paths = max_paths
    
    def resolve(self, reference_node: GNode, graph_roots: List[GNode]) -> List[ResolutionResult]:
        """
        Resolve a reference node to its definition(s).
        
        Args:
            reference_node: The PUSH node representing the reference to resolve
            graph_roots: List of root nodes in the graph to search
            
        Returns:
            List of ResolutionResult objects, one for each valid definition found
        """
        if reference_node.type != 'PUSH':
            logger.warning(f"Reference node is not a PUSH node: {reference_node.type}")
            return []
        
        if not graph_roots:
            logger.warning("No graph roots provided")
            return []
        
        logger.debug(f"Resolving reference: {reference_node.symbol} at ({reference_node.start_byte}, {reference_node.end_byte})")
        
        # Initialize state with the reference node
        initial_state = ResolutionState(
            current_node=reference_node,
            symbol_stack=[reference_node.symbol],
            scope_stack=[],
            path=[reference_node],
            visited={id(reference_node)}
        )
        
        # Use BFS to explore paths
        results: List[ResolutionResult] = []
        queue = deque([initial_state])
        paths_explored = 0
        
        while queue and paths_explored < self.max_paths:
            state = queue.popleft()
            paths_explored += 1
            
            # Check depth limit
            if len(state.path) > self.max_depth:
                logger.debug(f"Path exceeded max depth: {len(state.path)}")
                continue
            
            # Explore neighbors
            neighbors = self._get_neighbors(state.current_node, graph_roots)
            for neighbor in neighbors:
                if id(neighbor) in state.visited:
                    continue
                
                new_state = self._apply_transition(state, neighbor)
                if new_state:
                    # Check if we found a definition AFTER applying transition
                    # (POP node should have been processed and symbol stack should be empty)
                    if self._is_valid_definition_after_transition(new_state):
                        result = ResolutionResult(
                            definition=neighbor,  # The POP node we just processed
                            path=new_state.path.copy(),
                            confidence=self._calculate_confidence(new_state)
                        )
                        results.append(result)
                        logger.debug(f"Found definition: {neighbor.symbol} via path of length {len(new_state.path)}")
                        continue  # Don't explore further from this path
                    
                    # Continue exploring if state is valid
                    if self._is_valid_state(new_state):
                        queue.append(new_state)
        
        logger.info(f"Resolution complete: found {len(results)} definition(s) for {reference_node.symbol}")
        return results
    
    def _is_valid_definition_after_transition(self, state: ResolutionState) -> bool:
        """
        Check if state represents a valid definition match AFTER transition has been applied.
        
        This is called after a POP node transition, so the symbol should already be popped.
        A valid definition requires:
        - Current node is a POP node (the definition we just matched)
        - Symbol stack is empty (we successfully popped the matching symbol)
        - Scope stack can have elements (definition can be within scopes)
        """
        if state.current_node.type != 'POP':
            return False
        
        # After popping, symbol stack should be empty
        if len(state.symbol_stack) != 0:
            return False
        
        # Scope stack can have elements - definitions can be nested in scopes
        # This is valid as long as symbol stack is empty
        
        return True
    
    def _apply_transition(self, state: ResolutionState, next_node: GNode) -> Optional[ResolutionState]:
        """
        Apply a transition to a new node, updating stacks accordingly.
        
        Returns:
            New ResolutionState if transition is valid, None otherwise
        """
        # Create new state
        new_state = ResolutionState(
            current_node=next_node,
            symbol_stack=state.symbol_stack.copy(),
            scope_stack=state.scope_stack.copy(),
            path=state.path + [next_node],
            visited=state.visited.copy()
        )
        new_state.visited.add(id(next_node))
        
        node_type = next_node.type.strip()
        current_node = state.current_node
        
        # Determine if we're entering or exiting a scope
        # If current node is a SCOPE and next_node is its child, we're entering
        # If next_node is a SCOPE and current_node is its child, we're entering the scope
        # If we're going from child to parent SCOPE, we're exiting
        
        # Handle SCOPE nodes: manage scope stack based on direction
        if node_type == 'SCOPE':
            # Check if we're entering this scope (current node is parent of next_node)
            is_entering = current_node in next_node.parent if next_node.parent else False
            # Or if next_node contains current_node as child
            is_entering = is_entering or (current_node in next_node.children)
            
            if is_entering:
                # Entering scope: push to stack
                new_state.scope_stack.append(next_node)
            else:
                # Exiting scope: pop from stack if it matches
                if new_state.scope_stack and new_state.scope_stack[-1] == next_node:
                    new_state.scope_stack.pop()
                # If it doesn't match, we might be traversing incorrectly, but allow it
            return new_state
        
        # Handle PUSH nodes: add symbol to stack
        elif node_type == 'PUSH':
            # Only add if it's not the initial reference (which is already on stack)
            if not state.path or state.path[0] != next_node:
                new_state.symbol_stack.append(next_node.symbol)
            return new_state
        
        # Handle POP nodes: remove matching symbol from stack
        elif node_type == 'POP':
            if not new_state.symbol_stack:
                # Can't pop from empty stack
                return None
            
            # Check if symbol matches
            if next_node.symbol == new_state.symbol_stack[-1]:
                new_state.symbol_stack.pop()
                return new_state
            else:
                # Symbol doesn't match, can't continue this path
                return None
        
        # Other node types: just traverse (no stack changes)
        # But check if we're exiting a scope (going from child to parent SCOPE)
        else:
            # Check if current node's parent is a SCOPE we should exit
            if current_node.parent:
                for parent in current_node.parent:
                    if parent.type == 'SCOPE' and parent not in next_node.parent:
                        # We're leaving this scope
                        if new_state.scope_stack and new_state.scope_stack[-1] == parent:
                            new_state.scope_stack.pop()
            return new_state
    
    def _is_valid_state(self, state: ResolutionState) -> bool:
        """
        Check if a state is valid for continued exploration.
        
        A state is invalid if:
        - Symbol stack is empty and we're not at a definition
        - Symbol stack has too many elements (unlikely to resolve)
        - We've visited this node before in this path
        """
        # If symbol stack is empty and we're not at a POP, this path is dead
        if not state.symbol_stack and state.current_node.type != 'POP':
            return False
        
        # If symbol stack has too many elements, path is likely invalid
        if len(state.symbol_stack) > 10:  # Reasonable limit
            return False
        
        return True
    
    def _get_neighbors(self, node: GNode, graph_roots: List[GNode]) -> List[GNode]:
        """
        Get all neighbors of a node in the graph.
        
        Neighbors include:
        - Parent nodes (going up the hierarchy)
        - Child nodes (going down the hierarchy)
        - Sibling nodes in the same scope
        """
        neighbors: List[GNode] = []
        
        # Add parents
        if node.parent:
            neighbors.extend(node.parent)
        
        # Add children
        neighbors.extend(node.children)
        
        # Add siblings (nodes that share a parent)
        if node.parent:
            for parent in node.parent:
                for sibling in parent.children:
                    if sibling != node and id(sibling) not in [id(n) for n in neighbors]:
                        neighbors.append(sibling)
        
        return neighbors
    
    def _calculate_confidence(self, state: ResolutionState) -> float:
        """
        Calculate confidence score for a resolution result.
        
        Factors:
        - Shorter paths are more confident
        - Paths that don't traverse many scopes are more confident
        """
        path_length = len(state.path)
        scope_depth = len(state.scope_stack) if state.scope_stack else 0
        
        # Base confidence decreases with path length and scope depth
        base_confidence = 1.0
        length_penalty = min(path_length * 0.01, 0.3)  # Max 30% penalty
        scope_penalty = min(scope_depth * 0.05, 0.2)  # Max 20% penalty
        
        confidence = base_confidence - length_penalty - scope_penalty
        return max(0.5, confidence)  # Minimum 50% confidence
    
    def find_reference_by_position(self, graph_roots: List[GNode], line: int, column: int, 
                                   file_content: str) -> Optional[GNode]:
        """
        Find a reference node at a specific position in the source code.
        
        Args:
            graph_roots: Root nodes of the graph
            line: Line number (1-indexed)
            column: Column number (1-indexed)
            file_content: Source code content
            
        Returns:
            GNode if found, None otherwise
        """
        # Convert line/column to byte offset
        lines = file_content.split('\n')
        if line < 1 or line > len(lines):
            return None
        
        byte_offset = sum(len(l.encode('utf-8')) + 1 for l in lines[:line-1]) + (column - 1)
        
        # Search for PUSH nodes at this position
        def find_at_position(node: GNode) -> Optional[GNode]:
            if node.type == 'PUSH' and node.start_byte <= byte_offset <= node.end_byte:
                return node
            
            for child in node.children:
                result = find_at_position(child)
                if result:
                    return result
            
            return None
        
        for root in graph_roots:
            result = find_at_position(root)
            if result:
                return result
        
        return None
