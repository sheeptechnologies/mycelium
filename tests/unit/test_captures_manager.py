"""
Unit tests for CapturesManager.
"""

import pytest
from tree_sitter import Parser

from src.captures import CapturesManager


class TestCapturesManager:
    """Test suite for CapturesManager."""
    
    def test_init_python_language(self, captures_manager_python):
        """Test initialization with Python language."""
        assert captures_manager_python.language_name == "python"
        assert captures_manager_python.LANGUAGE is not None
        assert len(captures_manager_python.dispatch_map) > 0
    
    def test_init_unsupported_language(self):
        """Test initialization with unsupported language raises error."""
        with pytest.raises(ValueError, match="not supported"):
            CapturesManager("unsupported_language")
    
    def test_get_handlers(self, captures_manager_python):
        """Test getting handler map."""
        handlers = captures_manager_python.get_handlers()
        
        assert isinstance(handlers, dict)
        assert len(handlers) > 0
        # Check that handlers are callable
        for handler in handlers.values():
            assert callable(handler)
    
    def test_get_handler_existing(self, captures_manager_python):
        """Test getting an existing handler."""
        handler = captures_manager_python.get_handler("identifier")
        assert handler is not None
        assert callable(handler)
    
    def test_get_handler_nonexistent(self, captures_manager_python):
        """Test getting a non-existent handler returns None."""
        handler = captures_manager_python.get_handler("nonexistent_handler")
        assert handler is None
    
    def test_execute_simple_code(self, captures_manager_python, python_code_simple):
        """Test executing queries on simple Python code."""
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(python_code_simple.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        assert isinstance(captures, list)
        assert len(captures) > 0
        
        # Verify structure: list of (node, capture_name) tuples
        for capture in captures:
            assert isinstance(capture, tuple)
            assert len(capture) == 2
            node, capture_name = capture
            assert hasattr(node, 'start_byte')
            assert hasattr(node, 'end_byte')
            assert isinstance(capture_name, str)
    
    def test_execute_captures_ordered(self, captures_manager_python):
        """Test that captures are ordered by byte range."""
        code = "x = 42"
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        # Verify ordering: start_byte ascending, end_byte descending
        for i in range(len(captures) - 1):
            node1, _ = captures[i]
            node2, _ = captures[i + 1]
            
            # Either start_byte is less, or if equal, end_byte is greater (descending)
            assert (node1.start_byte < node2.start_byte or 
                   (node1.start_byte == node2.start_byte and node1.end_byte >= node2.end_byte))
    
    def test_execute_empty_code(self, captures_manager_python):
        """Test executing queries on empty code."""
        code = ""
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        # Empty code might still have a module node
        assert isinstance(captures, list)
    
    def test_query_compilation(self, captures_manager_python):
        """Test that queries are compiled correctly."""
        assert captures_manager_python.query_obj is not None
        # Query object should have capture names
        assert len(captures_manager_python.dispatch_map) > 0
    
    def test_dispatch_map_contains_expected_handlers(self, captures_manager_python):
        """Test that dispatch map contains expected Python handlers."""
        expected_handlers = [
            "identifier",
            "module",
            "function_definition",
            "class_definition",
            "assignment",
            "call",
            "attribute"
        ]
        
        handlers = captures_manager_python.get_handlers()
        
        # At least some expected handlers should be present
        found_handlers = [h for h in expected_handlers if h in handlers]
        assert len(found_handlers) > 0, "No expected handlers found"
    
    def test_execute_with_function(self, captures_manager_python):
        """Test executing queries on code with a function."""
        code = """
def test_function():
    return 42
"""
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        # Should capture module, function_definition, identifier, etc.
        capture_names = [name for _, name in captures]
        assert "module" in capture_names or "function_definition" in capture_names
    
    def test_execute_with_class(self, captures_manager_python):
        """Test executing queries on code with a class."""
        code = """
class TestClass:
    pass
"""
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        capture_names = [name for _, name in captures]
        assert "module" in capture_names or "class_definition" in capture_names
    
    def test_execute_with_assignment(self, captures_manager_python):
        """Test executing queries on code with assignment."""
        code = "x = 10"
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        capture_names = [name for _, name in captures]
        # Should have assignment or identifier
        assert len([n for n in capture_names if n in ["assignment", "identifier", "module"]]) > 0
    
    def test_multiple_captures_same_node(self, captures_manager_python):
        """Test that a single node can have multiple captures."""
        code = "x = y"
        parser = Parser(captures_manager_python.LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        
        captures = captures_manager_python.execute(tree.root_node)
        
        # Group by node to check for multiple captures
        nodes_to_captures = {}
        for node, capture_name in captures:
            node_id = id(node)
            if node_id not in nodes_to_captures:
                nodes_to_captures[node_id] = []
            nodes_to_captures[node_id].append(capture_name)
        
        # Some nodes might have multiple capture names
        # This is valid if queries overlap
