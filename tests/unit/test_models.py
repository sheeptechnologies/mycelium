"""
Unit tests for GNode model.
"""

import pytest

from src.models import GNode


class TestGNode:
    """Test suite for GNode dataclass."""
    
    def test_create_gnode_basic(self):
        """Test basic GNode creation."""
        node = GNode(
            symbol="test",
            type="SCOPE",
            start_byte=0,
            end_byte=10
        )
        
        assert node.symbol == "test"
        assert node.type == "SCOPE"
        assert node.start_byte == 0
        assert node.end_byte == 10
        assert node.children == []
        assert node.parent == []
        assert node.ctx == "PUSH"  # Default value
    
    def test_create_gnode_with_ctx(self):
        """Test GNode creation with custom ctx."""
        node = GNode(
            symbol="identifier",
            type="POP",
            ctx="identifier",
            start_byte=5,
            end_byte=15
        )
        
        assert node.ctx == "identifier"
        assert node.type == "POP"
    
    def test_gnode_default_children(self):
        """Test that children list is initialized as empty."""
        node = GNode(
            symbol="test",
            type="SCOPE",
            start_byte=0,
            end_byte=10
        )
        
        assert isinstance(node.children, list)
        assert len(node.children) == 0
    
    def test_gnode_default_parent(self):
        """Test that parent list is initialized as empty."""
        node = GNode(
            symbol="test",
            type="SCOPE",
            start_byte=0,
            end_byte=10
        )
        
        assert isinstance(node.parent, list)
        assert len(node.parent) == 0
    
    def test_gnode_add_child(self):
        """Test adding a child to a GNode."""
        parent = GNode(
            symbol="parent",
            type="SCOPE",
            start_byte=0,
            end_byte=20
        )
        
        child = GNode(
            symbol="child",
            type="POP",
            start_byte=5,
            end_byte=10
        )
        
        parent.children.append(child)
        child.parent.append(parent)
        
        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert len(child.parent) == 1
        assert child.parent[0] == parent
    
    def test_gnode_multiple_children(self):
        """Test adding multiple children to a GNode."""
        parent = GNode(
            symbol="parent",
            type="SCOPE",
            start_byte=0,
            end_byte=30
        )
        
        child1 = GNode(symbol="child1", type="POP", start_byte=5, end_byte=10)
        child2 = GNode(symbol="child2", type="PUSH", start_byte=15, end_byte=20)
        
        parent.children.extend([child1, child2])
        child1.parent.append(parent)
        child2.parent.append(parent)
        
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children
    
    def test_gnode_multiple_parents(self):
        """Test a node with multiple parents (uncommon but possible)."""
        child = GNode(
            symbol="child",
            type="POP",
            start_byte=5,
            end_byte=10
        )
        
        parent1 = GNode(symbol="parent1", type="SCOPE", start_byte=0, end_byte=20)
        parent2 = GNode(symbol="parent2", type="SCOPE", start_byte=0, end_byte=20)
        
        child.parent.extend([parent1, parent2])
        parent1.children.append(child)
        parent2.children.append(child)
        
        assert len(child.parent) == 2
        assert parent1 in child.parent
        assert parent2 in child.parent
    
    def test_gnode_repr(self):
        """Test GNode string representation."""
        node = GNode(
            symbol="test_symbol",
            type="SCOPE",
            start_byte=10,
            end_byte=25
        )
        
        repr_str = repr(node)
        assert "SCOPE" in repr_str
        assert "test_symbol" in repr_str
        assert "10" in repr_str
        assert "25" in repr_str
    
    def test_gnode_byte_range(self):
        """Test byte range properties."""
        node = GNode(
            symbol="test",
            type="SCOPE",
            start_byte=100,
            end_byte=200
        )
        
        assert node.start_byte == 100
        assert node.end_byte == 200
        assert node.end_byte > node.start_byte
    
    def test_gnode_types(self):
        """Test different node types."""
        scope_node = GNode(symbol="scope", type="SCOPE", start_byte=0, end_byte=10)
        push_node = GNode(symbol="push", type="PUSH", start_byte=0, end_byte=5)
        pop_node = GNode(symbol="pop", type="POP", start_byte=5, end_byte=10)
        
        assert scope_node.type == "SCOPE"
        assert push_node.type == "PUSH"
        assert pop_node.type == "POP"
    
    def test_gnode_nested_structure(self):
        """Test creating a nested structure of nodes."""
        root = GNode(symbol="root", type="SCOPE", start_byte=0, end_byte=100)
        
        level1 = GNode(symbol="level1", type="SCOPE", start_byte=10, end_byte=50)
        level2 = GNode(symbol="level2", type="SCOPE", start_byte=20, end_byte=30)
        leaf = GNode(symbol="leaf", type="POP", start_byte=25, end_byte=28)
        
        root.children.append(level1)
        level1.parent.append(root)
        
        level1.children.append(level2)
        level2.parent.append(level1)
        
        level2.children.append(leaf)
        leaf.parent.append(level2)
        
        # Verify structure
        assert len(root.children) == 1
        assert root.children[0] == level1
        assert len(level1.children) == 1
        assert level1.children[0] == level2
        assert len(level2.children) == 1
        assert level2.children[0] == leaf
        
        # Verify parent chain
        assert leaf.parent[0] == level2
        assert level2.parent[0] == level1
        assert level1.parent[0] == root
