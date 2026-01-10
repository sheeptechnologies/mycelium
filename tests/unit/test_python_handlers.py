"""
Unit tests for Python language handlers.
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.graph import GraphBuilder
from src.models import GNode
from src.languages.python.handlers import (
    handle_identifier,
    handle_module,
    handle_class_definition,
    handle_function_definition,
    handle_assignment,
    handle_call,
    handle_attribute,
    handle_lambda,
    handle_return_statement,
    handle_typed_parameter,
    handle_typed_default_parameter,
    propagate_type
)


class MockNode:
    """Mock Tree-sitter node for testing handlers."""
    def __init__(self, start_byte=0, end_byte=10, node_type="test", text=b"test"):
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.type = node_type
        self.text = text
    
    def child_by_field_name(self, name):
        """Mock method for getting child by field name."""
        return None
    
    @property
    def byte_range(self):
        """Return byte range tuple."""
        return (self.start_byte, self.end_byte)


class TestHandleIdentifier:
    """Test suite for handle_identifier."""
    
    def test_handle_identifier_basic(self):
        """Test basic identifier handling."""
        builder = GraphBuilder()
        node = MockNode(start_byte=0, end_byte=5, text=b"hello")
        
        result = handle_identifier(builder, node, [])
        
        assert isinstance(result, GNode)
        assert result.symbol == "hello"
        assert result.type == "POP"
        assert result.ctx == "identifier"
        assert result.start_byte == 0
        assert result.end_byte == 5
    
    def test_handle_identifier_unicode(self):
        """Test identifier with unicode characters."""
        builder = GraphBuilder()
        node = MockNode(start_byte=0, end_byte=10, text="café".encode('utf-8'))
        
        result = handle_identifier(builder, node, [])
        
        assert result.symbol == "café"


class TestHandleModule:
    """Test suite for handle_module."""
    
    def test_handle_module_basic(self):
        """Test basic module handling."""
        builder = GraphBuilder()
        node = MockNode(start_byte=0, end_byte=100, node_type="module")
        children = [
            GNode(symbol="child1", type="POP", start_byte=10, end_byte=20),
            GNode(symbol="child2", type="POP", start_byte=30, end_byte=40)
        ]
        
        result = handle_module(builder, node, children)
        
        assert isinstance(result, GNode)
        assert result.symbol == "module"
        assert result.type == "module"
        assert len(result.children) == 2
        assert result.children == children


class TestHandleClassDefinition:
    """Test suite for handle_class_definition."""
    
    def test_handle_class_definition_basic(self):
        """Test basic class definition handling."""
        builder = GraphBuilder()
        
        # Create mock class node with name field
        class_node = MockNode(start_byte=0, end_byte=50, node_type="class_definition")
        name_node = MockNode(start_byte=6, end_byte=12, text=b"MyClass")
        body_node = MockNode(start_byte=13, end_byte=48)
        
        def mock_child_by_field_name(name):
            if name == "name":
                return name_node
            elif name == "body":
                return body_node
            return None
        
        class_node.child_by_field_name = mock_child_by_field_name
        
        # Create identifier node for class name
        name_identifier = GNode(
            symbol="MyClass",
            type="POP",
            ctx="identifier",
            start_byte=6,
            end_byte=12
        )
        
        children = [name_identifier]
        
        result = handle_class_definition(builder, class_node, children)
        
        assert result is not None
        assert result.symbol == "class_scope"
        assert result.type == "SCOPE"


class TestHandleFunctionDefinition:
    """Test suite for handle_function_definition."""
    
    def test_handle_function_definition_basic(self):
        """Test basic function definition handling."""
        builder = GraphBuilder()
        
        func_node = MockNode(start_byte=0, end_byte=30, node_type="function_definition")
        name_node = MockNode(start_byte=4, end_byte=10, text=b"my_func")
        body_node = MockNode(start_byte=11, end_byte=28)
        
        def mock_child_by_field_name(name):
            if name == "name":
                return name_node
            elif name == "body":
                return body_node
            return None
        
        func_node.child_by_field_name = mock_child_by_field_name
        
        name_identifier = GNode(
            symbol="my_func",
            type="POP",
            ctx="identifier",
            start_byte=4,
            end_byte=10
        )
        
        children = [name_identifier]
        
        result = handle_function_definition(builder, func_node, children)
        
        assert result is not None
        assert result.symbol == "function_definition"
        assert result.type == "SCOPE"


class TestHandleAssignment:
    """Test suite for handle_assignment."""
    
    def test_handle_assignment_basic(self):
        """Test basic assignment handling."""
        builder = GraphBuilder()
        
        assign_node = MockNode(start_byte=0, end_byte=15, node_type="assignment")
        left_node = MockNode(start_byte=0, end_byte=5)
        right_node = MockNode(start_byte=8, end_byte=14)
        
        def mock_child_by_field_name(name):
            if name == "left":
                return left_node
            elif name == "right":
                return right_node
            return None
        
        assign_node.child_by_field_name = mock_child_by_field_name
        
        left_identifier = GNode(
            symbol="x",
            type="POP",
            ctx="identifier",
            start_byte=0,
            end_byte=5
        )
        right_identifier = GNode(
            symbol="y",
            type="POP",
            ctx="identifier",
            start_byte=8,
            end_byte=14
        )
        
        children = [left_identifier, right_identifier]
        
        result = handle_assignment(builder, assign_node, children)
        
        assert isinstance(result, list)
        assert len(result) == 2


class TestHandleCall:
    """Test suite for handle_call."""
    
    def test_handle_call_basic(self):
        """Test basic function call handling."""
        builder = GraphBuilder()
        
        call_node = MockNode(start_byte=0, end_byte=20, node_type="call")
        function_node = MockNode(start_byte=0, end_byte=8)
        arguments_node = MockNode(start_byte=9, end_byte=19)
        
        def mock_child_by_field_name(name):
            if name == "function":
                return function_node
            elif name == "arguments":
                return arguments_node
            return None
        
        call_node.child_by_field_name = mock_child_by_field_name
        
        func_identifier = GNode(
            symbol="func",
            type="POP",
            ctx="identifier",
            start_byte=0,
            end_byte=8
        )
        
        children = [func_identifier]
        
        result = handle_call(builder, call_node, children)
        
        assert result is not None
        assert result.symbol == "call"
        assert result.type == "SCOPE"
        assert result.ctx == "call"


class TestHandleAttribute:
    """Test suite for handle_attribute."""
    
    def test_handle_attribute_basic(self):
        """Test basic attribute access handling."""
        builder = GraphBuilder()
        
        attr_node = MockNode(start_byte=0, end_byte=15, node_type="attribute")
        object_node = MockNode(start_byte=0, end_byte=8)
        attribute_node = MockNode(start_byte=9, end_byte=14)
        
        def mock_child_by_field_name(name):
            if name == "object":
                return object_node
            elif name == "attribute":
                return attribute_node
            return None
        
        attr_node.child_by_field_name = mock_child_by_field_name
        
        obj_identifier = GNode(
            symbol="obj",
            type="POP",
            ctx="identifier",
            start_byte=0,
            end_byte=8
        )
        attr_identifier = GNode(
            symbol="attr",
            type="POP",
            ctx="identifier",
            start_byte=9,
            end_byte=14
        )
        
        children = [obj_identifier, attr_identifier]
        
        result = handle_attribute(builder, attr_node, children)
        
        assert result is not None


class TestHandleLambda:
    """Test suite for handle_lambda."""
    
    def test_handle_lambda_basic(self):
        """Test basic lambda handling."""
        builder = GraphBuilder()
        
        lambda_node = MockNode(start_byte=0, end_byte=20, node_type="lambda")
        children = [
            GNode(symbol="x", type="POP", start_byte=8, end_byte=9)
        ]
        
        result = handle_lambda(builder, lambda_node, children)
        
        assert result is not None
        assert result.symbol == "lambda"
        assert result.type == "SCOPE"
        assert len(result.children) == 1


class TestHandleReturnStatement:
    """Test suite for handle_return_statement."""
    
    def test_handle_return_statement_with_identifier(self):
        """Test return statement with identifier."""
        builder = GraphBuilder()
        
        return_node = MockNode(start_byte=0, end_byte=15, node_type="return_statement")
        identifier = GNode(
            symbol="value",
            type="POP",
            ctx="identifier",
            start_byte=7,
            end_byte=12
        )
        
        children = [identifier]
        
        result = handle_return_statement(builder, return_node, children)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "PUSH"  # Should be converted to PUSH


class TestHandleTypedParameter:
    """Test suite for handle_typed_parameter."""
    
    def test_handle_typed_parameter_basic(self):
        """Test typed parameter handling."""
        builder = GraphBuilder()
        
        param_node = MockNode(start_byte=0, end_byte=20, node_type="typed_parameter")
        name_node = GNode(symbol="x", type="POP", ctx="identifier", start_byte=0, end_byte=5)
        type_node = GNode(symbol="int", type="POP", ctx="identifier", start_byte=7, end_byte=10)
        
        children = [name_node, type_node]
        
        result = handle_typed_parameter(builder, param_node, children)
        
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].symbol == "x"
        assert result[0].type == "POP"


class TestPropagateType:
    """Test suite for propagate_type."""
    
    def test_propagate_type_single_node(self):
        """Test type propagation on a single node."""
        node = GNode(symbol="x", type="POP", start_byte=0, end_byte=5)
        
        propagate_type([node], "PUSH")
        
        assert node.type == "PUSH"
    
    def test_propagate_type_tree(self):
        """Test type propagation through a tree."""
        root = GNode(symbol="root", type="SCOPE", start_byte=0, end_byte=20)
        child1 = GNode(symbol="child1", type="POP", start_byte=5, end_byte=10)
        child2 = GNode(symbol="child2", type="POP", start_byte=12, end_byte=18)
        
        root.children = [child1, child2]
        child1.parent = [root]
        child2.parent = [root]
        
        propagate_type([root], "PUSH")
        
        # SCOPE nodes should not be changed
        assert root.type == "SCOPE"
        # But children should be changed
        assert child1.type == "PUSH"
        assert child2.type == "PUSH"
    
    def test_propagate_type_handles_cycles(self):
        """Test that propagate_type handles cycles correctly."""
        node1 = GNode(symbol="node1", type="POP", start_byte=0, end_byte=5)
        node2 = GNode(symbol="node2", type="POP", start_byte=5, end_byte=10)
        
        # Create a cycle
        node1.children = [node2]
        node2.children = [node1]
        node1.parent = [node2]
        node2.parent = [node1]
        
        # Should not cause infinite loop
        propagate_type([node1], "PUSH")
        
        assert node1.type == "PUSH"
        assert node2.type == "PUSH"
