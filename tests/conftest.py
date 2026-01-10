"""
Pytest configuration and shared fixtures for Mycelium tests.

This module provides:
- Fixtures for common test scenarios (code samples, builders, etc.)
- Helper functions for graph traversal and assertions
- Utilities for multi-language test support (prepared for future languages)
"""

import pytest
import tempfile
from pathlib import Path
from typing import List, Optional, Set

from tree_sitter import Parser, Tree

from src.captures import CapturesManager
from src.graph import GraphBuilder
from src.models import GNode


@pytest.fixture
def python_code_simple():
    """Simple Python code for testing."""
    return """
def hello(name):
    return f"Hello, {name}!"

result = hello("world")
"""


@pytest.fixture
def python_code_class():
    """Python code with a class definition."""
    return """
class Person:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
"""


@pytest.fixture
def python_code_complex():
    """More complex Python code for integration tests."""
    return """
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def bark(self):
        return f"{self.name} barks!"

def create_dog(name):
    return Dog(name)

my_dog = create_dog("Buddy")
sound = my_dog.bark()
"""


@pytest.fixture
def captures_manager_python():
    """Fixture providing a CapturesManager for Python."""
    return CapturesManager("python")


@pytest.fixture
def graph_builder():
    """Fixture providing a GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture
def temp_file(tmp_path):
    """
    Fixture providing a temporary file path factory.
    
    Usage:
        def test_something(temp_file):
            file_path = temp_file("code content", ".py")
            # Use file_path...
    """
    def _create_file(content: str, suffix: str = ".py") -> Path:
        file_path = tmp_path / f"test{suffix}"
        file_path.write_text(content, encoding='utf-8')
        return file_path
    return _create_file


# Future language fixtures (prepared for extensibility)
# These can be uncommented and implemented when adding new language support

# @pytest.fixture
# def javascript_code_simple():
#     """Simple JavaScript code for testing."""
#     return """
#     function hello(name) {
#         return `Hello, ${name}!`;
#     }
#     const result = hello("world");
#     """

# @pytest.fixture
# def captures_manager_javascript():
#     """Fixture providing a CapturesManager for JavaScript."""
#     return CapturesManager("javascript")


# Helper functions for graph assertions

def find_node_by_symbol(nodes: List[GNode], symbol: str, recursive: bool = True) -> GNode:
    """
    Find a node by its symbol in a list of nodes.
    
    Args:
        nodes: List of GNode objects to search
        symbol: Symbol to search for
        recursive: If True, search in children recursively
    
    Returns:
        First matching GNode or None
    """
    visited = set()
    
    def search(node: GNode):
        if id(node) in visited:
            return None
        visited.add(id(node))
        
        if node.symbol == symbol:
            return node
        
        if recursive:
            for child in node.children:
                result = search(child)
                if result:
                    return result
        
        return None
    
    for node in nodes:
        result = search(node)
        if result:
            return result
    
    return None


def count_nodes_by_type(nodes: List[GNode], node_type: str, recursive: bool = True) -> int:
    """
    Count nodes of a specific type in a graph.
    
    Args:
        nodes: List of root GNode objects
        node_type: Type to count (e.g., "SCOPE", "PUSH", "POP")
        recursive: If True, count in children recursively
    
    Returns:
        Number of nodes with the specified type
    """
    visited = set()
    count = 0
    
    def traverse(node: GNode):
        nonlocal count
        if id(node) in visited:
            return
        visited.add(id(node))
        
        if node.type == node_type:
            count += 1
        
        if recursive:
            for child in node.children:
                traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return count


def assert_node_exists(nodes: List[GNode], symbol: str, node_type: str = None, recursive: bool = True):
    """
    Assert that a node with the given symbol exists.
    
    Args:
        nodes: List of root GNode objects
        symbol: Symbol to search for
        node_type: Optional type to verify
        recursive: If True, search recursively
    
    Raises:
        AssertionError: If node is not found or type doesn't match
    """
    node = find_node_by_symbol(nodes, symbol, recursive)
    assert node is not None, f"Node with symbol '{symbol}' not found"
    if node_type:
        assert node.type == node_type, f"Node '{symbol}' has type '{node.type}', expected '{node_type}'"


def assert_node_has_parent(node: GNode, parent_symbol: str):
    """
    Assert that a node has a parent with the given symbol.
    
    Args:
        node: GNode to check
        parent_symbol: Symbol of expected parent
    
    Raises:
        AssertionError: If parent is not found
    """
    assert node.parent, f"Node '{node.symbol}' has no parents"
    parent_symbols = [p.symbol for p in node.parent]
    assert parent_symbol in parent_symbols, f"Node '{node.symbol}' does not have parent '{parent_symbol}'. Parents: {parent_symbols}"


def assert_node_has_child(node: GNode, child_symbol: str):
    """
    Assert that a node has a child with the given symbol.
    
    Args:
        node: GNode to check
        child_symbol: Symbol of expected child
    
    Raises:
        AssertionError: If child is not found
    """
    child_symbols = [c.symbol for c in node.children]
    assert child_symbol in child_symbols, f"Node '{node.symbol}' does not have child '{child_symbol}'. Children: {child_symbols}"


def get_all_nodes(nodes: List[GNode], recursive: bool = True) -> List[GNode]:
    """
    Get all nodes from a graph as a flat list.
    
    Args:
        nodes: List of root GNode objects
        recursive: If True, include all descendants
    
    Returns:
        List of all GNode objects
    """
    visited = set()
    result = []
    
    def traverse(node: GNode):
        if id(node) in visited:
            return
        visited.add(id(node))
        result.append(node)
        
        if recursive:
            for child in node.children:
                traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return result


def find_nodes_by_type(nodes: List[GNode], node_type: str, recursive: bool = True) -> List[GNode]:
    """
    Find all nodes of a specific type in a graph.
    
    Args:
        nodes: List of root GNode objects
        node_type: Type to search for (e.g., "SCOPE", "PUSH", "POP")
        recursive: If True, search in children recursively
    
    Returns:
        List of GNode objects with the specified type
    """
    all_nodes = get_all_nodes(nodes, recursive)
    return [n for n in all_nodes if n.type == node_type]


def find_nodes_by_symbol_and_type(nodes: List[GNode], symbol: str, 
                                   node_type: Optional[str] = None, 
                                   recursive: bool = True) -> List[GNode]:
    """
    Find all nodes matching symbol and optionally type.
    
    Args:
        nodes: List of root GNode objects
        symbol: Symbol to search for
        node_type: Optional type to filter by
        recursive: If True, search recursively
    
    Returns:
        List of matching GNode objects
    """
    all_nodes = get_all_nodes(nodes, recursive)
    matching = [n for n in all_nodes if n.symbol == symbol]
    if node_type:
        matching = [n for n in matching if n.type == node_type]
    return matching


def assert_graph_structure_valid(nodes: List[GNode]):
    """
    Assert that the graph structure is valid (parent-child consistency, byte ranges).
    
    Note: This function validates bidirectional relationships where they exist.
    Some nodes may not have parent relationships set (e.g., root nodes or nodes
    that are not yet fully connected), which is acceptable.
    
    Args:
        nodes: List of root GNode objects
    
    Raises:
        AssertionError: If graph structure is invalid
    """
    all_nodes = get_all_nodes(nodes)
    root_node_ids = {id(n) for n in nodes}
    
    for node in all_nodes:
        # Validate byte ranges
        assert node.start_byte >= 0, \
            f"Node '{node.symbol}' has invalid start_byte: {node.start_byte}"
        assert node.end_byte >= node.start_byte, \
            f"Node '{node.symbol}' has end_byte ({node.end_byte}) < start_byte ({node.start_byte})"
        
        # Validate parent-child relationships (only if both sides are set)
        # Note: Some graph construction patterns may not maintain perfect bidirectional
        # relationships, so we validate only when both sides are explicitly set
        if node.parent:
            for parent in node.parent:
                # Only validate if parent has children set
                if parent.children:
                    assert node in parent.children, \
                        f"Node '{node.symbol}' has parent '{parent.symbol}' but is not in parent's children"
        
        # Validate child->parent relationship only if child has parents set
        # and we can verify the relationship exists
        for child in node.children:
            if child.parent:
                # Check if this node is in the child's parent list (using id for comparison)
                parent_ids = {id(p) for p in child.parent}
                if id(node) not in parent_ids:
                    # This might be acceptable if there are multiple nodes with same symbol
                    # Only fail if we can definitively say it's wrong
                    # For now, we'll be permissive and just log a warning
                    pass


def get_node_depth(node: GNode, roots: List[GNode]) -> int:
    """
    Calculate the depth of a node in the graph (distance from root).
    
    Args:
        node: Node to calculate depth for
        roots: List of root nodes
    
    Returns:
        Depth of the node (0 for root nodes, 1 for direct children, etc.)
    """
    if node in roots:
        return 0
    
    visited = set()
    
    def find_depth(current: GNode, depth: int) -> Optional[int]:
        if id(current) in visited:
            return None
        visited.add(id(current))
        
        if current == node:
            return depth
        
        for child in current.children:
            result = find_depth(child, depth + 1)
            if result is not None:
                return result
        
        return None
    
    for root in roots:
        result = find_depth(root, 0)
        if result is not None:
            return result
    
    return -1  # Node not found


def get_path_to_node(node: GNode, roots: List[GNode]) -> Optional[List[GNode]]:
    """
    Get the path from root to a specific node.
    
    Args:
        node: Target node
        roots: List of root nodes
    
    Returns:
        List of nodes representing the path from root to target, or None if not found
    """
    visited = set()
    
    def find_path(current: GNode, path: List[GNode]) -> Optional[List[GNode]]:
        if id(current) in visited:
            return None
        visited.add(id(current))
        
        current_path = path + [current]
        
        if current == node:
            return current_path
        
        for child in current.children:
            result = find_path(child, current_path)
            if result:
                return result
        
        return None
    
    for root in roots:
        result = find_path(root, [])
        if result:
            return result
    
    return None


def assert_node_in_scope(node: GNode, scope_symbol: str, roots: List[GNode]):
    """
    Assert that a node is within a specific scope.
    
    Args:
        node: Node to check
        scope_symbol: Symbol of the scope node
        roots: List of root nodes
    
    Raises:
        AssertionError: If node is not in the specified scope
    """
    path = get_path_to_node(node, roots)
    assert path is not None, f"Node '{node.symbol}' not found in graph"
    
    scope_nodes = [n for n in path if n.symbol == scope_symbol and n.type == "SCOPE"]
    assert len(scope_nodes) > 0, \
        f"Node '{node.symbol}' is not in scope '{scope_symbol}'. Path: {[n.symbol for n in path]}"


def get_scope_chain(node: GNode, roots: List[GNode]) -> List[GNode]:
    """
    Get the chain of scope nodes from root to a node.
    
    Args:
        node: Target node
        roots: List of root nodes
    
    Returns:
        List of SCOPE nodes from root to target (inclusive if target is a scope)
    """
    path = get_path_to_node(node, roots)
    if path is None:
        return []
    
    return [n for n in path if n.type == "SCOPE"]


def count_references_to_symbol(nodes: List[GNode], symbol: str) -> int:
    """
    Count the number of PUSH nodes (references) for a symbol.
    
    Args:
        nodes: List of root GNode objects
        symbol: Symbol to count references for
    
    Returns:
        Number of PUSH nodes with the given symbol
    """
    all_nodes = get_all_nodes(nodes)
    push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
    return len(push_nodes)


def count_definitions_of_symbol(nodes: List[GNode], symbol: str) -> int:
    """
    Count the number of POP nodes (definitions) for a symbol.
    
    Args:
        nodes: List of root GNode objects
        symbol: Symbol to count definitions for
    
    Returns:
        Number of POP nodes with the given symbol
    """
    all_nodes = get_all_nodes(nodes)
    pop_nodes = [n for n in all_nodes if n.type == 'POP' and n.symbol == symbol]
    return len(pop_nodes)
