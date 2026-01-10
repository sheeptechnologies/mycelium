"""
Abstract base classes for graph construction tests.

These classes define the interface and common patterns for testing
stack graph construction across different programming languages.
"""

from abc import ABC, abstractmethod
from typing import List
import pytest

from src.graph_builder import StackGraphBuilder
from src.models import GNode
from tests.conftest import get_all_nodes, count_nodes_by_type, find_node_by_symbol


class BaseGraphTestSuite(ABC):
    """
    Abstract base class for language-specific graph construction test suites.
    
    Subclasses should implement the `get_language()` method and can
    override setup methods if needed. All test methods should follow
    the patterns defined here for consistency.
    """
    
    @abstractmethod
    def get_language(self) -> str:
        """
        Return the language identifier (e.g., 'python', 'javascript').
        
        Returns:
            Language identifier string
        """
        pass
    
    def create_builder(self) -> StackGraphBuilder:
        """
        Create a StackGraphBuilder instance for the test language.
        
        Returns:
            StackGraphBuilder configured for the test language
        """
        return StackGraphBuilder(language=self.get_language())
    
    def build_graph(self, code: str) -> List[GNode]:
        """
        Build a stack graph from source code.
        
        Args:
            code: Source code string
            
        Returns:
            List of root nodes in the graph
        """
        builder = self.create_builder()
        return builder.build_from_code(code)
    
    def assert_graph_not_empty(self, roots: List[GNode], min_nodes: int = 1):
        """
        Assert that the graph is not empty.
        
        Args:
            roots: Root nodes of the graph
            min_nodes: Minimum number of nodes expected
            
        Raises:
            AssertionError: If graph is too small
        """
        assert len(roots) > 0, "Graph should have at least one root node"
        all_nodes = get_all_nodes(roots)
        assert len(all_nodes) >= min_nodes, \
            f"Graph should have at least {min_nodes} nodes (found {len(all_nodes)})"
    
    def assert_node_exists(self, roots: List[GNode], symbol: str, 
                          node_type: Optional[str] = None):
        """
        Assert that a node with the given symbol exists.
        
        Args:
            roots: Root nodes of the graph
            symbol: Symbol to search for
            node_type: Optional node type to verify
            
        Raises:
            AssertionError: If node is not found or type doesn't match
        """
        node = find_node_by_symbol(roots, symbol)
        assert node is not None, f"Node with symbol '{symbol}' not found"
        if node_type:
            assert node.type == node_type, \
                f"Node '{symbol}' has type '{node.type}', expected '{node_type}'"
    
    def assert_node_count(self, roots: List[GNode], node_type: str, 
                         expected_count: int, exact: bool = False):
        """
        Assert the count of nodes of a specific type.
        
        Args:
            roots: Root nodes of the graph
            node_type: Type of nodes to count
            expected_count: Expected count
            exact: If True, count must match exactly; if False, count must be >= expected
            
        Raises:
            AssertionError: If count doesn't match expectations
        """
        actual_count = count_nodes_by_type(roots, node_type)
        if exact:
            assert actual_count == expected_count, \
                f"Expected exactly {expected_count} nodes of type '{node_type}', found {actual_count}"
        else:
            assert actual_count >= expected_count, \
                f"Expected at least {expected_count} nodes of type '{node_type}', found {actual_count}"
    
    def assert_scope_structure(self, roots: List[GNode], min_scopes: int = 1):
        """
        Assert that the graph has proper scope structure.
        
        Args:
            roots: Root nodes of the graph
            min_scopes: Minimum number of SCOPE nodes expected
            
        Raises:
            AssertionError: If scope structure is invalid
        """
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count >= min_scopes, \
            f"Graph should have at least {min_scopes} SCOPE nodes (found {scope_count})"
    
    def assert_graph_consistency(self, roots: List[GNode]):
        """
        Assert that the graph structure is consistent (parent-child relationships).
        
        Args:
            roots: Root nodes of the graph
            
        Raises:
            AssertionError: If graph structure is inconsistent
        """
        all_nodes = get_all_nodes(roots)
        
        for node in all_nodes:
            # If node has parents, each parent should have this node as child
            if node.parent:
                for parent in node.parent:
                    assert node in parent.children, \
                        f"Node '{node.symbol}' has parent '{parent.symbol}' but is not in parent's children"
            
            # If node has children, each child should have this node as parent
            for child in node.children:
                assert node in child.parent, \
                    f"Node '{node.symbol}' has child '{child.symbol}' but is not in child's parents"
            
            # Validate byte ranges
            assert node.start_byte >= 0, \
                f"Node '{node.symbol}' has invalid start_byte: {node.start_byte}"
            assert node.end_byte >= node.start_byte, \
                f"Node '{node.symbol}' has end_byte ({node.end_byte}) < start_byte ({node.start_byte})"
    
    def assert_all_nodes_have_valid_ranges(self, roots: List[GNode]):
        """
        Assert that all nodes have valid byte ranges.
        
        Args:
            roots: Root nodes of the graph
            
        Raises:
            AssertionError: If any node has invalid byte ranges
        """
        all_nodes = get_all_nodes(roots)
        for node in all_nodes:
            assert node.start_byte >= 0, \
                f"Node '{node.symbol}' has invalid start_byte: {node.start_byte}"
            assert node.end_byte >= node.start_byte, \
                f"Node '{node.symbol}' has end_byte ({node.end_byte}) < start_byte ({node.start_byte})"
