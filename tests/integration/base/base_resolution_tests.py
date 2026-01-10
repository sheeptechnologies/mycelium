"""
Abstract base classes for reference resolution tests.

These classes define the interface and common patterns for testing
reference resolution across different programming languages.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import pytest

from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import get_all_nodes


class BaseResolutionTestSuite(ABC):
    """
    Abstract base class for language-specific resolution test suites.
    
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
    
    def create_resolver(self, max_depth: int = 1000, max_paths: int = 100) -> ReferenceResolver:
        """
        Create a ReferenceResolver instance with optional limits.
        
        Args:
            max_depth: Maximum depth for path traversal
            max_paths: Maximum number of paths to explore
            
        Returns:
            ReferenceResolver instance
        """
        return ReferenceResolver(max_depth=max_depth, max_paths=max_paths)
    
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
    
    def find_push_nodes(self, roots: List[GNode], symbol: str) -> List[GNode]:
        """
        Find all PUSH nodes with the given symbol.
        
        Args:
            roots: Root nodes of the graph
            symbol: Symbol to search for
            
        Returns:
            List of PUSH nodes matching the symbol
        """
        all_nodes = get_all_nodes(roots)
        return [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
    
    def find_pop_nodes(self, roots: List[GNode], symbol: str) -> List[GNode]:
        """
        Find all POP nodes with the given symbol.
        
        Args:
            roots: Root nodes of the graph
            symbol: Symbol to search for
            
        Returns:
            List of POP nodes matching the symbol
        """
        all_nodes = get_all_nodes(roots)
        return [n for n in all_nodes if n.type == 'POP' and n.symbol == symbol]
    
    def resolve_reference(self, roots: List[GNode], symbol: str, 
                         reference_index: int = 0) -> List[ResolutionResult]:
        """
        Resolve a reference to its definition(s).
        
        Args:
            roots: Root nodes of the graph
            symbol: Symbol to resolve
            reference_index: Index of the reference to resolve (if multiple exist)
            
        Returns:
            List of ResolutionResult objects
        """
        push_nodes = self.find_push_nodes(roots, symbol)
        assert len(push_nodes) > reference_index, \
            f"Not enough PUSH nodes for symbol '{symbol}' (found {len(push_nodes)}, need {reference_index + 1})"
        
        resolver = self.create_resolver()
        return resolver.resolve(push_nodes[reference_index], roots)
    
    def assert_resolution_success(self, results: List[ResolutionResult], 
                                   expected_symbol: str,
                                   min_confidence: float = 0.0) -> ResolutionResult:
        """
        Assert that resolution was successful and return the first result.
        
        Args:
            results: List of resolution results
            expected_symbol: Expected symbol name
            min_confidence: Minimum confidence threshold
            
        Returns:
            First resolution result
            
        Raises:
            AssertionError: If resolution failed or doesn't match expectations
        """
        assert len(results) > 0, f"Expected at least one resolution result for '{expected_symbol}'"
        
        result = results[0]
        assert result.definition.type == 'POP', \
            f"Definition should be a POP node, got {result.definition.type}"
        assert result.definition.symbol == expected_symbol, \
            f"Definition symbol mismatch: expected '{expected_symbol}', got '{result.definition.symbol}'"
        assert len(result.path) > 0, "Resolution path should not be empty"
        assert result.confidence >= min_confidence, \
            f"Confidence {result.confidence} below minimum {min_confidence}"
        
        # Verify path structure
        assert result.path[0].type == 'PUSH', "Path should start with PUSH node"
        assert result.path[-1].type == 'POP', "Path should end with POP node"
        
        return result
    
    def assert_resolution_failure(self, results: List[ResolutionResult]):
        """
        Assert that resolution failed (no results found).
        
        Args:
            results: List of resolution results (should be empty)
            
        Raises:
            AssertionError: If results are not empty
        """
        assert len(results) == 0, f"Expected no resolution results, but got {len(results)}"
    
    def assert_all_references_resolve_to_same(self, roots: List[GNode], symbol: str):
        """
        Assert that all references to a symbol resolve to the same definition.
        
        Args:
            roots: Root nodes of the graph
            symbol: Symbol to check
            
        Raises:
            AssertionError: If references resolve to different definitions
        """
        push_nodes = self.find_push_nodes(roots, symbol)
        assert len(push_nodes) >= 2, \
            f"Need at least 2 references to '{symbol}' to test consistency (found {len(push_nodes)})"
        
        resolver = self.create_resolver()
        definitions = set()
        
        for push_node in push_nodes:
            results = resolver.resolve(push_node, roots)
            assert len(results) > 0, \
                f"Reference at byte {push_node.start_byte} should resolve"
            definitions.add(id(results[0].definition))
        
        assert len(definitions) == 1, \
            f"All references to '{symbol}' should resolve to the same definition (found {len(definitions)} different definitions)"
    
    def assert_byte_range_valid(self, node: GNode):
        """
        Assert that a node has valid byte ranges.
        
        Args:
            node: Node to validate
            
        Raises:
            AssertionError: If byte ranges are invalid
        """
        assert node.start_byte >= 0, \
            f"Node '{node.symbol}' has invalid start_byte: {node.start_byte}"
        assert node.end_byte >= node.start_byte, \
            f"Node '{node.symbol}' has end_byte ({node.end_byte}) < start_byte ({node.start_byte})"
    
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
            self.assert_byte_range_valid(node)
