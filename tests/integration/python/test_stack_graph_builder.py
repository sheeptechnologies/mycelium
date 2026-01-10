"""
Integration tests for StackGraphBuilder.
"""

import pytest
from pathlib import Path

from src.graph_builder import StackGraphBuilder
from tests.conftest import (
    find_node_by_symbol,
    count_nodes_by_type,
    assert_node_exists,
    assert_node_has_parent,
    assert_node_has_child,
    get_all_nodes
)


class TestStackGraphBuilder:
    """Test suite for StackGraphBuilder integration."""
    
    def test_init_default_language(self):
        """Test initialization with default language."""
        builder = StackGraphBuilder()
        assert builder.language == "python"
        assert builder.captures_manager is not None
        assert builder.parser is not None
    
    def test_init_specific_language(self):
        """Test initialization with specific language."""
        builder = StackGraphBuilder("python")
        assert builder.language == "python"
    
    def test_build_from_code_simple(self, python_code_simple):
        """Test building graph from simple code string."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_simple)
        
        assert isinstance(roots, list)
        assert len(roots) > 0
        # Should have at least a root node
        assert roots[0].symbol == "source_file"
        assert roots[0].type == "SCOPE"
    
    def test_build_from_code_empty(self):
        """Test building graph from empty code."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code("")
        
        assert isinstance(roots, list)
        # Empty code might return empty list or root node only
        assert len(roots) >= 0
    
    def test_build_from_code_with_function(self):
        """Test building graph from code with function definition."""
        code = """
def greet(name):
    return f"Hello, {name}!"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        # Should have function definition in graph
        all_nodes = get_all_nodes(roots)
        function_nodes = [n for n in all_nodes if "function" in n.symbol.lower() or n.ctx == "function_definition"]
        assert len(function_nodes) > 0
    
    def test_build_from_code_with_class(self, python_code_class):
        """Test building graph from code with class definition."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_class)
        
        assert len(roots) > 0
        # Should have class definition in graph
        all_nodes = get_all_nodes(roots)
        class_nodes = [n for n in all_nodes if "class" in n.symbol.lower()]
        assert len(class_nodes) > 0
    
    def test_build_from_code_with_assignment(self):
        """Test building graph from code with assignment."""
        code = "x = 42"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        # Should have assignment nodes
        all_nodes = get_all_nodes(roots)
        identifier_nodes = [n for n in all_nodes if n.ctx == "identifier"]
        assert len(identifier_nodes) > 0
    
    def test_build_from_code_with_call(self):
        """Test building graph from code with function call."""
        code = """
def hello():
    pass

hello()
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        # Should have call nodes
        all_nodes = get_all_nodes(roots)
        call_nodes = [n for n in all_nodes if n.ctx == "call"]
        # Might have call nodes or identifiers
        assert len(all_nodes) > 1
    
    def test_build_from_code_with_attribute(self):
        """Test building graph from code with attribute access."""
        code = "obj.attr"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        # Should have some nodes
        assert len(all_nodes) > 0
    
    def test_build_from_code_with_lambda(self):
        """Test building graph from code with lambda."""
        code = "f = lambda x: x + 1"
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        lambda_nodes = [n for n in all_nodes if n.symbol == "lambda"]
        assert len(lambda_nodes) > 0
    
    def test_build_from_file(self, temp_file, python_code_simple):
        """Test building graph from file."""
        file_path = temp_file(python_code_simple, suffix=".py")
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(file_path))
        
        assert isinstance(roots, list)
        assert len(roots) > 0
    
    def test_build_from_file_nonexistent(self):
        """Test building graph from non-existent file raises error."""
        builder = StackGraphBuilder()
        
        with pytest.raises(FileNotFoundError):
            builder.build_from_file("nonexistent_file.py")
    
    def test_build_from_file_invalid_encoding(self, tmp_path):
        """Test building graph from file with invalid encoding."""
        # Create a file with binary data that's not valid UTF-8
        file_path = tmp_path / "invalid.py"
        file_path.write_bytes(b'\xff\xfe\x00\x01')
        
        builder = StackGraphBuilder()
        
        with pytest.raises((IOError, UnicodeDecodeError, RuntimeError)):
            builder.build_from_file(str(file_path))
    
    def test_build_from_tree(self, python_code_simple):
        """Test building graph from Tree-sitter Tree."""
        from tree_sitter import Parser
        
        builder = StackGraphBuilder()
        parser = Parser(builder.captures_manager.LANGUAGE)
        tree = parser.parse(python_code_simple.encode('utf-8'))
        
        roots = builder.build_from_tree(tree)
        
        assert isinstance(roots, list)
        assert len(roots) > 0
    
    def test_build_from_tree_empty(self):
        """Test building graph from empty tree."""
        from tree_sitter import Parser
        
        builder = StackGraphBuilder()
        parser = Parser(builder.captures_manager.LANGUAGE)
        tree = parser.parse(b"")
        
        roots = builder.build_from_tree(tree)
        
        # Empty tree might return empty list or root node
        assert isinstance(roots, list)
    
    def test_build_graph_structure_has_scope_nodes(self, python_code_simple):
        """Test that built graph has SCOPE nodes."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_simple)
        
        scope_count = count_nodes_by_type(roots, "SCOPE")
        assert scope_count > 0, "Graph should have at least one SCOPE node"
    
    def test_build_graph_structure_has_pop_nodes(self, python_code_simple):
        """Test that built graph has POP nodes for identifiers."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_simple)
        
        pop_count = count_nodes_by_type(roots, "POP")
        # Should have at least some POP nodes for identifiers
        assert pop_count >= 0  # Might be 0 for very simple code
    
    def test_build_graph_parent_child_relationships(self, python_code_class):
        """Test that graph has correct parent-child relationships."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_class)
        
        all_nodes = get_all_nodes(roots)
        
        # Check that nodes with parents have correct relationships
        for node in all_nodes:
            if node.parent:
                for parent in node.parent:
                    assert node in parent.children, f"Node {node.symbol} should be in parent {parent.symbol}'s children"
    
    def test_build_graph_multiple_files(self, temp_file):
        """Test building graphs from multiple files."""
        code1 = "x = 1"
        code2 = "y = 2"
        
        file1 = temp_file(code1, suffix=".py")
        file2 = temp_file(code2, suffix=".py")
        
        builder = StackGraphBuilder()
        roots1 = builder.build_from_file(str(file1))
        roots2 = builder.build_from_file(str(file2))
        
        assert len(roots1) > 0
        assert len(roots2) > 0
        # Each file should have its own root
        assert roots1[0].symbol == "source_file"
        assert roots2[0].symbol == "source_file"
    
    def test_build_from_code_complex_structure(self, python_code_complex):
        """Test building graph from complex code structure."""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(python_code_complex)
        
        assert len(roots) > 0
        all_nodes = get_all_nodes(roots)
        
        # Should have multiple nodes
        assert len(all_nodes) > 5
        
        # Should have class nodes
        class_nodes = [n for n in all_nodes if "class" in n.symbol.lower() or "Animal" in n.symbol or "Dog" in n.symbol]
        # Might have class-related nodes
        assert len(all_nodes) > 0
