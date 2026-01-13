"""
Public API for building stack graphs from source code.

This module provides the StackGraphBuilder class, which is the main entry point
for creating stack graphs from source files or code strings.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from tree_sitter import Parser, Tree

from .captures import CapturesManager
from .graph import GraphBuilder
from .models import GNode

logger = logging.getLogger(__name__)


class StackGraphBuilder:
    """
    High-level API for building stack graphs from source code.
    
    This class encapsulates the full pipeline:
    1. Parse source code using Tree-sitter
    2. Extract relevant AST nodes using queries
    3. Build stack graph using handlers
    """
    
    def __init__(self, language: str = "python"):
        """
        Initialize the stack graph builder for a specific language.
        
        Args:
            language: The programming language (e.g., "python", "javascript")
        
        Raises:
            ValueError: If the language is not supported
            RuntimeError: If the Tree-sitter language cannot be loaded
        """
        self.language = language
        self.captures_manager = CapturesManager(language)
        self.parser = Parser(self.captures_manager.LANGUAGE)
        logger.info(f"Initialized StackGraphBuilder for language: {language}")
    
    def build_from_file(self, file_path: str) -> List[GNode]:
        """
        Build a stack graph from a source file.
        
        Args:
            file_path: Path to the source file
        
        Returns:
            List of root GNode objects representing the stack graph
        
        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If the file cannot be read
            RuntimeError: If parsing or graph building fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            code = path.read_text(encoding='utf-8')
            logger.debug(f"Read {len(code)} bytes from {file_path}")
            return self.build_from_code(code)
        except UnicodeDecodeError as e:
            raise IOError(f"Failed to decode file {file_path} as UTF-8: {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading file {file_path}: {e}")
    
    def build_from_code(self, code: str) -> List[GNode]:
        """
        Build a stack graph from a code string.
        
        Args:
            code: Source code as a string
        
        Returns:
            List of root GNode objects representing the stack graph
        
        Raises:
            RuntimeError: If parsing or graph building fails
        """
        if not code:
            logger.warning("Empty code string provided, returning empty graph")
            return []
        
        try:
            tree = self.parser.parse(code.encode('utf-8'))
            return self.build_from_tree(tree, code)
        except Exception as e:
            logger.error(f"Error parsing code: {e}")
            raise RuntimeError(f"Failed to parse code: {e}")

    def _parse_module_sections(self, code: str):
        sections = []
        offset = 0
        current = None
        for line in code.splitlines(keepends=True):
            match = re.match(r'#\s*-+\s*path:\s*(.+?)\s*-*\s*$', line)
            if match:
                if current:
                    current["end"] = offset
                module_path = self._module_path_from_file(match.group(1).strip())
                current = {
                    "start": offset + len(line),
                    "end": None,
                    "module_path": module_path,
                }
                sections.append(current)
            offset += len(line)
        if current:
            current["end"] = len(code)
        return sections

    def _module_path_from_file(self, path: str) -> List[str]:
        parts = [p for p in path.replace('\\n', '').split('/') if p]
        if not parts:
            return []
        filename = parts[-1]
        if filename.endswith('.py'):
            filename = filename[:-3]
        if filename == '__init__':
            parts = parts[:-1]
        else:
            parts[-1] = filename
        return [p for p in parts if p]
    
    def build_from_tree(self, tree: Tree, code: Optional[str] = None) -> List[GNode]:
        """
        Build a stack graph from a Tree-sitter Tree object.
        
        This method is useful for advanced use cases where you already have
        a parsed tree, or for testing purposes.
        
        Args:
            tree: A Tree-sitter Tree object
        
        Returns:
            List of root GNode objects representing the stack graph
        
        Raises:
            RuntimeError: If graph building fails
        """
        if not tree or not tree.root_node:
            logger.warning("Empty or invalid tree provided")
            return []
        
        try:
            # Execute queries to get captures
            captures = self.captures_manager.execute(tree.root_node)
            logger.debug(f"Extracted {len(captures)} captures from tree")
            
            # Get handler map
            handler_map = self.captures_manager.get_handlers()
            
            # Build graph
            builder = GraphBuilder()
            if code:
                sections = self._parse_module_sections(code)
                if sections:
                    builder.set_module_sections(sections)
            root_nodes = builder.build(captures, handler_map)
            
            logger.info(f"Built stack graph with {len(root_nodes)} root node(s)")
            return root_nodes
        except Exception as e:
            logger.error(f"Error building graph from tree: {e}")
            raise RuntimeError(f"Failed to build graph: {e}")
