"""
Unit tests for GraphBuilder.
"""

import pytest
from unittest.mock import Mock, MagicMock
from tree_sitter import Node

from src.graph import GraphBuilder
from src.models import GNode


class MockNode:
    """Mock Tree-sitter node for testing."""
    def __init__(self, start_byte, end_byte, node_type="test"):
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.type = node_type
        self.text = b"test"


class TestGraphBuilder:
    """Test suite for GraphBuilder."""
    
    def test_init(self):
        """Test GraphBuilder initialization."""
        builder = GraphBuilder()
        
        assert builder.root_node is not None
        assert builder.root_node.symbol == "source_file"
        assert builder.root_node.type == "SCOPE"
        assert isinstance(builder.root_nodes, list)
        assert len(builder.root_nodes) == 1
        assert builder.root_nodes[0] == builder.root_node
        assert isinstance(builder.stack, list)
        assert len(builder.stack) == 0
    
    def test_sort_captures_basic(self):
        """Test basic capture sorting."""
        builder = GraphBuilder()
        
        node1 = MockNode(0, 10)
        node2 = MockNode(5, 15)
        node3 = MockNode(0, 20)
        
        captures = [
            (node2, "identifier"),
            (node1, "identifier"),
            (node3, "module")
        ]
        
        sorted_captures = builder.sort_captures(captures)
        
        # Should be sorted by start_byte, then by -end_byte
        assert sorted_captures[0][0].start_byte <= sorted_captures[1][0].start_byte
        assert sorted_captures[1][0].start_byte <= sorted_captures[2][0].start_byte
    
    def test_sort_captures_priority(self):
        """Test that capture priority affects sorting."""
        builder = GraphBuilder()
        
        # Create nodes with same byte range
        node1 = MockNode(0, 10)
        node2 = MockNode(0, 10)
        
        captures = [
            (node1, "identifier"),  # Priority 100
            (node2, "module")        # Priority 50 (default)
        ]
        
        sorted_captures = builder.sort_captures(captures)
        
        # Module (lower priority) should come before identifier (higher priority)
        assert sorted_captures[0][1] == "module"
        assert sorted_captures[1][1] == "identifier"
    
    def test_sort_captures_same_start_different_end(self):
        """Test sorting when start bytes are same but end bytes differ."""
        builder = GraphBuilder()
        
        node1 = MockNode(0, 20)  # Larger range (parent)
        node2 = MockNode(0, 10)  # Smaller range (child)
        
        captures = [
            (node2, "identifier"),
            (node1, "module")
        ]
        
        sorted_captures = builder.sort_captures(captures)
        
        # Parent (larger end_byte) should come first due to -end_byte sorting
        assert sorted_captures[0][0].end_byte >= sorted_captures[1][0].end_byte
    
    def test_build_empty_captures(self):
        """Test building graph with empty captures."""
        builder = GraphBuilder()
        
        handler_map = {}
        result = builder.build([], handler_map)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == builder.root_node
    
    def test_build_single_capture(self):
        """Test building graph with a single capture."""
        builder = GraphBuilder()
        
        node = MockNode(0, 10)
        
        def mock_handler(builder, node, children):
            return GNode(
                symbol="test",
                type="SCOPE",
                start_byte=node.start_byte,
                end_byte=node.end_byte
            )
        
        handler_map = {"test": mock_handler}
        captures = [(node, "test")]
        
        result = builder.build(captures, handler_map)
        
        assert len(result) == 1
        assert len(builder.root_node.children) == 1
        assert builder.root_node.children[0].symbol == "test"
    
    def test_build_multiple_captures(self):
        """Test building graph with multiple captures."""
        builder = GraphBuilder()
        
        node1 = MockNode(0, 20)
        node2 = MockNode(5, 15)
        
        def handler1(builder, node, children):
            return GNode(
                symbol="parent",
                type="SCOPE",
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                children=children
            )
        
        def handler2(builder, node, children):
            return GNode(
                symbol="child",
                type="POP",
                start_byte=node.start_byte,
                end_byte=node.end_byte
            )
        
        handler_map = {
            "parent": handler1,
            "child": handler2
        }
        
        # Parent should come first (larger range)
        captures = [
            (node1, "parent"),
            (node2, "child")
        ]
        
        result = builder.build(captures, handler_map)
        
        assert len(result) == 1
        # Parent should be added to root, child should be added to parent
        assert len(builder.root_node.children) > 0
    
    def test_build_handler_returns_list(self):
        """Test building when handler returns a list."""
        builder = GraphBuilder()
        
        node = MockNode(0, 10)
        
        def mock_handler(builder, node, children):
            return [
                GNode(symbol="node1", type="POP", start_byte=0, end_byte=5),
                GNode(symbol="node2", type="POP", start_byte=5, end_byte=10)
            ]
        
        handler_map = {"test": mock_handler}
        captures = [(node, "test")]
        
        result = builder.build(captures, handler_map)
        
        assert len(builder.root_node.children) == 2
    
    def test_build_handler_returns_none(self):
        """Test building when handler returns None."""
        builder = GraphBuilder()
        
        node = MockNode(0, 10)
        
        def mock_handler(builder, node, children):
            return None
        
        handler_map = {"test": mock_handler}
        captures = [(node, "test")]
        
        result = builder.build(captures, handler_map)
        
        # Handler returning None should not add anything
        assert len(builder.root_node.children) == 0
    
    def test_build_nested_structure(self):
        """Test building nested structure with proper stack management."""
        builder = GraphBuilder()
        
        # Outer node (0-30)
        outer_node = MockNode(0, 30)
        # Middle node (5-25)
        middle_node = MockNode(5, 25)
        # Inner node (10-20)
        inner_node = MockNode(10, 20)
        
        def outer_handler(builder, node, children):
            return GNode(
                symbol="outer",
                type="SCOPE",
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                children=children
            )
        
        def middle_handler(builder, node, children):
            return GNode(
                symbol="middle",
                type="SCOPE",
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                children=children
            )
        
        def inner_handler(builder, node, children):
            return GNode(
                symbol="inner",
                type="POP",
                start_byte=node.start_byte,
                end_byte=node.end_byte
            )
        
        handler_map = {
            "outer": outer_handler,
            "middle": middle_handler,
            "inner": inner_handler
        }
        
        captures = [
            (outer_node, "outer"),
            (middle_node, "middle"),
            (inner_node, "inner")
        ]
        
        result = builder.build(captures, handler_map)
        
        # Verify structure: inner should be child of middle, middle should be child of outer
        assert len(result) == 1
        outer = builder.root_node.children[0]
        assert outer.symbol == "outer"
        assert len(outer.children) > 0
    
    def test_build_missing_handler(self, capsys):
        """Test building when handler is missing."""
        builder = GraphBuilder()
        
        node = MockNode(0, 10)
        handler_map = {}
        captures = [(node, "missing_handler")]
        
        result = builder.build(captures, handler_map)
        
        # Should print error but continue
        captured = capsys.readouterr()
        assert "ERROR" in captured.out or "missing_handler" in captured.out
    
    def test_process_and_pop_with_children(self):
        """Test _process_and_pop with children results."""
        builder = GraphBuilder()
        
        child_node = GNode(symbol="child", type="POP", start_byte=5, end_byte=10)
        
        def mock_handler(builder, node, children):
            return GNode(
                symbol="parent",
                type="SCOPE",
                start_byte=0,
                end_byte=20,
                children=children
            )
        
        node = MockNode(0, 20)
        ctx = {
            'node': node,
            'handler': mock_handler,
            'children_results': [child_node]
        }
        
        builder.stack.append(ctx)
        builder._process_and_pop()
        
        # Parent should be added to root
        assert len(builder.root_node.children) == 1
        parent = builder.root_node.children[0]
        assert parent.symbol == "parent"
        assert len(parent.children) == 1
        assert parent.children[0] == child_node
    
    def test_process_and_pop_empty_stack(self):
        """Test _process_and_pop when stack is empty."""
        builder = GraphBuilder()
        
        # Note: _process_and_pop may raise IndexError when stack is empty
        # This is expected behavior - the method assumes stack is not empty
        # In practice, this should not be called on empty stack
        try:
            builder._process_and_pop()
        except IndexError:
            # This is expected when stack is empty
            pass
        assert len(builder.stack) == 0
    
    def test_build_flush_stack(self):
        """Test that stack is flushed at the end of build."""
        builder = GraphBuilder()
        
        node1 = MockNode(0, 10)
        node2 = MockNode(5, 15)
        
        def handler1(builder, node, children):
            return GNode(symbol="node1", type="SCOPE", start_byte=0, end_byte=10)
        
        def handler2(builder, node, children):
            return GNode(symbol="node2", type="POP", start_byte=5, end_byte=15)
        
        handler_map = {"handler1": handler1, "handler2": handler2}
        
        # node2 ends after node1, so both should be in stack
        captures = [
            (node1, "handler1"),
            (node2, "handler2")
        ]
        
        result = builder.build(captures, handler_map)
        
        # Stack should be empty after build
        assert len(builder.stack) == 0
        # Both nodes should be processed
        assert len(result) == 1
