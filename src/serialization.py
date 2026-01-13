"""
Graph Serialization Module

Provides portable JSON serialization for stack graphs.
Completely standalone - no database dependencies.
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .models import GNode


class GraphSerializer:
    """
    Serialize and deserialize GNode graphs to/from JSON.

    Features:
    - Deterministic IDs via BFS traversal
    - Cycle-safe (uses ID references, not object refs)
    - Versioned schema for backward compatibility
    - Validatable structure
    """

    VERSION = "1.0.0"

    def serialize_graph(
        self,
        root_nodes: List[GNode],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Serialize graph to JSON string.

        Args:
            root_nodes: List of root GNode objects
            metadata: Optional metadata dict (file_path, language, etc.)

        Returns:
            JSON string representation

        Example:
            >>> serializer = GraphSerializer()
            >>> json_str = serializer.serialize_graph([root], {"file": "example.py"})
        """
        if not root_nodes:
            raise ValueError("root_nodes cannot be empty")

        # 1. Assign stable IDs via BFS
        node_to_id = self._assign_stable_ids(root_nodes)

        # 2. Collect all nodes in graph
        all_nodes = self._collect_nodes(root_nodes)

        # 3. Build node list with ID references
        nodes_data = []
        for node in all_nodes:
            node_id = node_to_id[id(node)]
            nodes_data.append({
                "id": node_id,
                "symbol": node.symbol,
                "type": node.type,
                "ctx": getattr(node, 'ctx', ''),
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "children": [node_to_id[id(child)] for child in node.children],
                "parent": [node_to_id[id(p)] for p in node.parent]
            })

        # 4. Build root IDs list
        root_ids = [node_to_id[id(root)] for root in root_nodes]

        # 5. Build metadata with timestamp
        final_metadata = metadata or {}
        if "timestamp" not in final_metadata:
            final_metadata["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # 6. Build final structure
        data = {
            "version": self.VERSION,
            "metadata": final_metadata,
            "nodes": nodes_data,
            "roots": root_ids
        }

        return json.dumps(data, indent=2)

    def deserialize_graph(
        self,
        json_str: str,
        validate: bool = True
    ) -> Tuple[List[GNode], Dict[str, Any]]:
        """
        Deserialize graph from JSON string.

        Args:
            json_str: JSON string
            validate: Whether to validate schema (default True)

        Returns:
            Tuple of (list of root GNode objects, metadata dict)

        Raises:
            ValueError: If JSON is invalid or schema validation fails

        Example:
            >>> serializer = GraphSerializer()
            >>> roots, metadata = serializer.deserialize_graph(json_str)
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if validate:
            self._validate_schema(data)

        # 1. Check version compatibility
        version = data.get("version", "1.0.0")
        if not self._is_compatible_version(version):
            raise ValueError(f"Incompatible schema version: {version}")

        # 2. Create all nodes first (without connections)
        id_to_node = {}
        for node_data in data["nodes"]:
            node = GNode(
                symbol=node_data["symbol"],
                type=node_data["type"],
                start_byte=node_data["start_byte"],
                end_byte=node_data["end_byte"],
                ctx=node_data.get("ctx", "")
            )
            id_to_node[node_data["id"]] = node

        # 3. Restore connections
        for node_data in data["nodes"]:
            node = id_to_node[node_data["id"]]
            node.children = [id_to_node[cid] for cid in node_data["children"]]
            node.parent = [id_to_node[pid] for pid in node_data["parent"]]

        # 4. Return roots and metadata
        roots = [id_to_node[rid] for rid in data["roots"]]
        metadata = data.get("metadata", {})

        return roots, metadata

    def _assign_stable_ids(self, roots: List[GNode]) -> Dict[int, int]:
        """
        Assign stable IDs via BFS traversal.

        Args:
            roots: List of root nodes

        Returns:
            Dict mapping node object id() to stable integer ID
        """
        node_to_id = {}
        next_id = 0
        visited = set()
        queue = list(roots)

        while queue:
            node = queue.pop(0)
            node_id_key = id(node)

            if node_id_key in visited:
                continue
            visited.add(node_id_key)

            node_to_id[node_id_key] = next_id
            next_id += 1

            # Add children to queue
            queue.extend(node.children)

        return node_to_id

    def _collect_nodes(self, roots: List[GNode]) -> List[GNode]:
        """
        Collect all nodes in graph via BFS.

        Args:
            roots: List of root nodes

        Returns:
            List of all nodes in graph
        """
        all_nodes = []
        visited = set()
        queue = list(roots)

        while queue:
            node = queue.pop(0)
            if id(node) in visited:
                continue
            visited.add(id(node))

            all_nodes.append(node)
            queue.extend(node.children)

        return all_nodes

    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate JSON schema.

        Args:
            data: Parsed JSON data

        Raises:
            ValueError: If schema is invalid
        """
        # Check top-level fields
        required_fields = ["version", "metadata", "nodes", "roots"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate nodes array
        if not isinstance(data["nodes"], list):
            raise ValueError("'nodes' must be an array")

        for i, node in enumerate(data["nodes"]):
            required_node_fields = ["id", "symbol", "type", "start_byte", "end_byte", "children", "parent"]
            for field in required_node_fields:
                if field not in node:
                    raise ValueError(f"Node {i} missing required field: {field}")

            # Validate field types
            if not isinstance(node["id"], int):
                raise ValueError(f"Node {i} 'id' must be integer")
            if not isinstance(node["children"], list):
                raise ValueError(f"Node {i} 'children' must be array")
            if not isinstance(node["parent"], list):
                raise ValueError(f"Node {i} 'parent' must be array")

        # Validate roots array
        if not isinstance(data["roots"], list):
            raise ValueError("'roots' must be an array")

        # Validate all node IDs exist
        node_ids = {node["id"] for node in data["nodes"]}
        for root_id in data["roots"]:
            if root_id not in node_ids:
                raise ValueError(f"Root ID {root_id} not found in nodes")

        # Validate all child/parent references exist
        for node in data["nodes"]:
            for child_id in node["children"]:
                if child_id not in node_ids:
                    raise ValueError(f"Child ID {child_id} not found in nodes")
            for parent_id in node["parent"]:
                if parent_id not in node_ids:
                    raise ValueError(f"Parent ID {parent_id} not found in nodes")

    def _is_compatible_version(self, version: str) -> bool:
        """
        Check if version is compatible with current serializer.

        Args:
            version: Version string (e.g. "1.0.0")

        Returns:
            True if compatible, False otherwise
        """
        try:
            major = int(version.split('.')[0])
            current_major = int(self.VERSION.split('.')[0])
            return major == current_major
        except (ValueError, IndexError):
            return False


# Convenience functions for common use cases

def serialize_graph(
    roots: List[GNode],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Serialize graph to JSON string.

    Convenience wrapper around GraphSerializer.serialize_graph().

    Args:
        roots: List of root GNode objects
        metadata: Optional metadata dict

    Returns:
        JSON string

    Example:
        >>> json_str = serialize_graph([root], {"file": "example.py"})
    """
    serializer = GraphSerializer()
    return serializer.serialize_graph(roots, metadata)


def deserialize_graph(
    json_str: str,
    validate: bool = True
) -> Tuple[List[GNode], Dict[str, Any]]:
    """
    Deserialize graph from JSON string.

    Convenience wrapper around GraphSerializer.deserialize_graph().

    Args:
        json_str: JSON string
        validate: Whether to validate schema

    Returns:
        Tuple of (list of root nodes, metadata dict)

    Example:
        >>> roots, metadata = deserialize_graph(json_str)
    """
    serializer = GraphSerializer()
    return serializer.deserialize_graph(json_str, validate)


def save_graph(
    roots: List[GNode],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save graph to JSON file.

    Args:
        roots: List of root GNode objects
        output_path: Path to output JSON file
        metadata: Optional metadata dict

    Example:
        >>> save_graph([root], "graph.json", {"file": "example.py"})
    """
    json_str = serialize_graph(roots, metadata)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_str)


def load_graph(
    input_path: str,
    validate: bool = True
) -> Tuple[List[GNode], Dict[str, Any]]:
    """
    Load graph from JSON file.

    Args:
        input_path: Path to input JSON file
        validate: Whether to validate schema

    Returns:
        Tuple of (list of root nodes, metadata dict)

    Example:
        >>> roots, metadata = load_graph("graph.json")
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        json_str = f.read()
    return deserialize_graph(json_str, validate)


def compute_graph_hash(roots: List[GNode]) -> str:
    """
    Compute SHA256 hash of serialized graph.

    Useful for detecting changes in graphs.

    Args:
        roots: List of root GNode objects

    Returns:
        Hex string of SHA256 hash

    Example:
        >>> hash1 = compute_graph_hash([root])
        >>> # ... modify graph ...
        >>> hash2 = compute_graph_hash([root])
        >>> if hash1 != hash2:
        >>>     print("Graph changed!")
    """
    json_str = serialize_graph(roots, metadata={})
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
