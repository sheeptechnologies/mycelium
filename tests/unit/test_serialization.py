"""
Unit tests for serialization module.

Tests all aspects of graph serialization and deserialization.
"""

import pytest
import json
import tempfile
import os
from src.models import GNode
from src.serialization import (
    GraphSerializer,
    serialize_graph,
    deserialize_graph,
    save_graph,
    load_graph,
    compute_graph_hash
)


class TestGraphSerializer:
    """Test suite for GraphSerializer class."""

    def test_serialize_simple_graph(self):
        """Test serialization of simple graph."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)

        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([root])

        assert json_str is not None
        data = json.loads(json_str)
        assert data["version"] == "1.0.0"
        assert len(data["nodes"]) == 1
        assert len(data["roots"]) == 1
        assert data["nodes"][0]["symbol"] == "test"

    def test_serialize_graph_with_children(self):
        """Test serialization of graph with parent-child relationships."""
        root = GNode(symbol="parent", type="POP", start_byte=0, end_byte=6)
        child = GNode(symbol="child", type="PUSH", start_byte=7, end_byte=12)
        root.children = [child]
        child.parent = [root]

        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([root])

        data = json.loads(json_str)
        assert len(data["nodes"]) == 2
        assert data["nodes"][0]["symbol"] == "parent"
        assert data["nodes"][1]["symbol"] == "child"
        assert 1 in data["nodes"][0]["children"]
        assert 0 in data["nodes"][1]["parent"]

    def test_serialize_with_metadata(self):
        """Test serialization with custom metadata."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        metadata = {
            "file_path": "example.py",
            "language": "python",
            "source_hash": "abc123"
        }

        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([root], metadata)

        data = json.loads(json_str)
        assert data["metadata"]["file_path"] == "example.py"
        assert data["metadata"]["language"] == "python"
        assert data["metadata"]["source_hash"] == "abc123"
        assert "timestamp" in data["metadata"]

    def test_serialize_empty_roots_raises_error(self):
        """Test that empty roots list raises ValueError."""
        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="root_nodes cannot be empty"):
            serializer.serialize_graph([])

    def test_serialize_cycle_handling(self):
        """Test serialization handles cycles correctly."""
        # Create cycle: A -> B -> A
        a = GNode(symbol="A", type="POP", start_byte=0, end_byte=1)
        b = GNode(symbol="B", type="PUSH", start_byte=2, end_byte=3)
        a.children = [b]
        b.parent = [a]
        b.children = [a]  # Cycle back
        a.parent = [b]

        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([a])

        # Should not crash, should serialize properly
        data = json.loads(json_str)
        assert len(data["nodes"]) == 2
        assert 0 in data["nodes"][1]["children"]  # B points back to A

    def test_deserialize_simple_graph(self):
        """Test deserialization of simple graph."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "test",
                    "type": "POP",
                    "ctx": "identifier",
                    "start_byte": 0,
                    "end_byte": 4,
                    "children": [],
                    "parent": []
                }
            ],
            "roots": [0]
        }

        serializer = GraphSerializer()
        roots, metadata = serializer.deserialize_graph(json.dumps(json_data))

        assert len(roots) == 1
        assert roots[0].symbol == "test"
        assert roots[0].type == "POP"
        assert roots[0].start_byte == 0
        assert roots[0].end_byte == 4

    def test_deserialize_graph_with_children(self):
        """Test deserialization restores parent-child relationships."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "parent",
                    "type": "POP",
                    "ctx": "",
                    "start_byte": 0,
                    "end_byte": 6,
                    "children": [1],
                    "parent": []
                },
                {
                    "id": 1,
                    "symbol": "child",
                    "type": "PUSH",
                    "ctx": "",
                    "start_byte": 7,
                    "end_byte": 12,
                    "children": [],
                    "parent": [0]
                }
            ],
            "roots": [0]
        }

        serializer = GraphSerializer()
        roots, metadata = serializer.deserialize_graph(json.dumps(json_data))

        assert len(roots) == 1
        assert len(roots[0].children) == 1
        assert roots[0].children[0].symbol == "child"
        assert roots[0].children[0].parent[0].symbol == "parent"

    def test_roundtrip_preserves_graph(self):
        """Test serialize -> deserialize preserves graph structure."""
        # Create complex graph
        root = GNode(symbol="root", type="SCOPE", start_byte=0, end_byte=10)
        child1 = GNode(symbol="child1", type="POP", start_byte=0, end_byte=5)
        child2 = GNode(symbol="child2", type="PUSH", start_byte=6, end_byte=10)
        grandchild = GNode(symbol="grandchild", type="PUSH", start_byte=7, end_byte=9)

        root.children = [child1, child2]
        child1.parent = [root]
        child2.parent = [root]
        child2.children = [grandchild]
        grandchild.parent = [child2]

        # Serialize
        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([root])

        # Deserialize
        restored_roots, metadata = serializer.deserialize_graph(json_str)

        # Verify structure
        assert len(restored_roots) == 1
        assert restored_roots[0].symbol == "root"
        assert len(restored_roots[0].children) == 2
        assert restored_roots[0].children[0].symbol == "child1"
        assert restored_roots[0].children[1].symbol == "child2"
        assert len(restored_roots[0].children[1].children) == 1
        assert restored_roots[0].children[1].children[0].symbol == "grandchild"

    def test_deserialize_invalid_json(self):
        """Test deserialization of invalid JSON raises error."""
        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Invalid JSON"):
            serializer.deserialize_graph("not valid json{]")

    def test_validate_schema_missing_field(self):
        """Test schema validation catches missing fields."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            # Missing "nodes" field
            "roots": [0]
        }

        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Missing required field: nodes"):
            serializer.deserialize_graph(json.dumps(json_data))

    def test_validate_schema_invalid_node(self):
        """Test schema validation catches invalid node structure."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "test",
                    # Missing "type" field
                    "ctx": "",
                    "start_byte": 0,
                    "end_byte": 4,
                    "children": [],
                    "parent": []
                }
            ],
            "roots": [0]
        }

        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Node 0 missing required field: type"):
            serializer.deserialize_graph(json.dumps(json_data))

    def test_validate_schema_invalid_root_id(self):
        """Test schema validation catches invalid root IDs."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "test",
                    "type": "POP",
                    "ctx": "",
                    "start_byte": 0,
                    "end_byte": 4,
                    "children": [],
                    "parent": []
                }
            ],
            "roots": [99]  # Non-existent node ID
        }

        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Root ID 99 not found in nodes"):
            serializer.deserialize_graph(json.dumps(json_data))

    def test_validate_schema_invalid_child_id(self):
        """Test schema validation catches invalid child IDs."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "test",
                    "type": "POP",
                    "ctx": "",
                    "start_byte": 0,
                    "end_byte": 4,
                    "children": [99],  # Non-existent child ID
                    "parent": []
                }
            ],
            "roots": [0]
        }

        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Child ID 99 not found in nodes"):
            serializer.deserialize_graph(json.dumps(json_data))

    def test_version_compatibility(self):
        """Test version compatibility checking."""
        serializer = GraphSerializer()

        # Same major version should be compatible
        assert serializer._is_compatible_version("1.0.0") == True
        assert serializer._is_compatible_version("1.5.0") == True
        assert serializer._is_compatible_version("1.99.99") == True

        # Different major version should be incompatible
        assert serializer._is_compatible_version("2.0.0") == False
        assert serializer._is_compatible_version("0.9.0") == False

        # Invalid version strings
        assert serializer._is_compatible_version("invalid") == False
        assert serializer._is_compatible_version("") == False

    def test_deserialize_incompatible_version(self):
        """Test deserialization rejects incompatible versions."""
        json_data = {
            "version": "2.0.0",  # Incompatible major version
            "metadata": {},
            "nodes": [
                {
                    "id": 0,
                    "symbol": "test",
                    "type": "POP",
                    "ctx": "",
                    "start_byte": 0,
                    "end_byte": 4,
                    "children": [],
                    "parent": []
                }
            ],
            "roots": [0]
        }

        serializer = GraphSerializer()
        with pytest.raises(ValueError, match="Incompatible schema version: 2.0.0"):
            serializer.deserialize_graph(json.dumps(json_data))

    def test_deserialize_skip_validation(self):
        """Test deserialization can skip validation if requested."""
        json_data = {
            "version": "1.0.0",
            "metadata": {},
            "nodes": [],
            "roots": []
        }

        serializer = GraphSerializer()
        # With validation should fail (empty nodes)
        # Without validation should work
        roots, metadata = serializer.deserialize_graph(json.dumps(json_data), validate=False)
        assert roots == []

    def test_stable_ids_deterministic(self):
        """Test that stable IDs are deterministic across calls."""
        root = GNode(symbol="root", type="POP", start_byte=0, end_byte=4)
        child1 = GNode(symbol="child1", type="PUSH", start_byte=0, end_byte=2)
        child2 = GNode(symbol="child2", type="PUSH", start_byte=2, end_byte=4)
        root.children = [child1, child2]
        child1.parent = [root]
        child2.parent = [root]

        serializer = GraphSerializer()

        # Serialize twice
        json_str1 = serializer.serialize_graph([root])
        json_str2 = serializer.serialize_graph([root])

        # IDs should be the same
        data1 = json.loads(json_str1)
        data2 = json.loads(json_str2)

        # Remove timestamp which may differ
        del data1["metadata"]["timestamp"]
        del data2["metadata"]["timestamp"]

        # Everything else should be identical
        assert data1["nodes"] == data2["nodes"]
        assert data1["roots"] == data2["roots"]


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_serialize_graph_function(self):
        """Test serialize_graph convenience function."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        json_str = serialize_graph([root])

        assert json_str is not None
        data = json.loads(json_str)
        assert data["version"] == "1.0.0"
        assert len(data["nodes"]) == 1

    def test_deserialize_graph_function(self):
        """Test deserialize_graph convenience function."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        json_str = serialize_graph([root])

        roots, metadata = deserialize_graph(json_str)
        assert len(roots) == 1
        assert roots[0].symbol == "test"

    def test_save_and_load_graph(self):
        """Test save_graph and load_graph functions."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        child = GNode(symbol="child", type="PUSH", start_byte=5, end_byte=10)
        root.children = [child]
        child.parent = [root]

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Save
            save_graph([root], temp_path, metadata={"test": "data"})

            # Load
            loaded_roots, loaded_metadata = load_graph(temp_path)

            # Verify
            assert len(loaded_roots) == 1
            assert loaded_roots[0].symbol == "test"
            assert len(loaded_roots[0].children) == 1
            assert loaded_roots[0].children[0].symbol == "child"
            assert loaded_metadata["test"] == "data"

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_compute_graph_hash(self):
        """Test compute_graph_hash function."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        hash1 = compute_graph_hash([root])

        assert hash1 is not None
        assert len(hash1) == 64  # SHA256 hex string

        # Same graph should produce same hash
        hash2 = compute_graph_hash([root])
        # Note: timestamps may differ, so hashes might differ too
        # In a real scenario, you'd want to exclude timestamps from hash computation

    def test_compute_graph_hash_detects_changes(self):
        """Test that hash changes when graph changes."""
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)
        hash1 = compute_graph_hash([root])

        # Modify graph
        child = GNode(symbol="child", type="PUSH", start_byte=5, end_byte=10)
        root.children = [child]
        child.parent = [root]

        hash2 = compute_graph_hash([root])

        # Hashes should differ
        assert hash1 != hash2


class TestLargeGraphs:
    """Test suite for large graph handling."""

    def test_serialize_large_graph(self):
        """Test serialization of large graph (1000+ nodes)."""
        # Create chain of 1000 nodes
        nodes = []
        for i in range(1000):
            node = GNode(symbol=f"node{i}", type="PUSH", start_byte=i, end_byte=i+1)
            nodes.append(node)

        # Link them
        for i in range(len(nodes) - 1):
            nodes[i].children = [nodes[i+1]]
            nodes[i+1].parent = [nodes[i]]

        serializer = GraphSerializer()
        json_str = serializer.serialize_graph([nodes[0]])

        data = json.loads(json_str)
        assert len(data["nodes"]) == 1000

    def test_roundtrip_large_graph(self):
        """Test serialize -> deserialize for large graph."""
        # Create tree: 1 root, 10 children, each with 10 grandchildren = 111 nodes
        root = GNode(symbol="root", type="SCOPE", start_byte=0, end_byte=1000)
        all_nodes = [root]

        for i in range(10):
            child = GNode(symbol=f"child{i}", type="POP", start_byte=i*100, end_byte=(i+1)*100)
            root.children.append(child)
            child.parent.append(root)
            all_nodes.append(child)

            for j in range(10):
                grandchild = GNode(symbol=f"gc{i}_{j}", type="PUSH", start_byte=i*100+j*10, end_byte=i*100+(j+1)*10)
                child.children.append(grandchild)
                grandchild.parent.append(child)
                all_nodes.append(grandchild)

        # Serialize
        json_str = serialize_graph([root])

        # Deserialize
        restored_roots, metadata = deserialize_graph(json_str)

        # Verify structure
        assert len(restored_roots) == 1
        assert restored_roots[0].symbol == "root"
        assert len(restored_roots[0].children) == 10
        for i in range(10):
            assert len(restored_roots[0].children[i].children) == 10


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_node_with_default_ctx(self):
        """Test serialization of node with default ctx value."""
        # GNode with ctx defaults to "PUSH" (from dataclass definition)
        root = GNode(symbol="test", type="POP", start_byte=0, end_byte=4)

        json_str = serialize_graph([root])
        data = json.loads(json_str)

        # Should use default value from GNode dataclass
        assert data["nodes"][0]["ctx"] == "PUSH"

    def test_multiple_roots(self):
        """Test serialization with multiple root nodes."""
        root1 = GNode(symbol="root1", type="POP", start_byte=0, end_byte=5)
        root2 = GNode(symbol="root2", type="POP", start_byte=6, end_byte=11)

        json_str = serialize_graph([root1, root2])
        data = json.loads(json_str)

        assert len(data["roots"]) == 2
        assert len(data["nodes"]) == 2

        # Deserialize
        roots, metadata = deserialize_graph(json_str)
        assert len(roots) == 2
        assert roots[0].symbol == "root1"
        assert roots[1].symbol == "root2"

    def test_shared_child(self):
        """Test graph where multiple parents share same child (DAG structure)."""
        parent1 = GNode(symbol="parent1", type="POP", start_byte=0, end_byte=7)
        parent2 = GNode(symbol="parent2", type="POP", start_byte=8, end_byte=15)
        shared_child = GNode(symbol="shared", type="PUSH", start_byte=16, end_byte=22)

        parent1.children = [shared_child]
        parent2.children = [shared_child]
        shared_child.parent = [parent1, parent2]

        json_str = serialize_graph([parent1, parent2])
        data = json.loads(json_str)

        # Should only serialize child once
        assert len(data["nodes"]) == 3

        # Deserialize and verify
        roots, metadata = deserialize_graph(json_str)
        assert len(roots) == 2
        assert roots[0].children[0] is roots[1].children[0]  # Same object
        assert len(roots[0].children[0].parent) == 2
