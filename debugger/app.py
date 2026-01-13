"""
Flask backend for web debugger interface.

Provides API endpoints for loading codebases, building stack graphs,
and resolving references to definitions.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path to import src modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from flask import Flask, render_template, request, jsonify

from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import get_all_nodes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Cache per grafi (per evitare rebuild continui)
# Key: file_path, Value: (graph_roots, code_hash)
graph_cache: Dict[str, tuple] = {}


def scan_python_files(directory: str) -> List[Dict[str, str]]:
    """
    Scan directory for Python files.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        List of dicts with 'name' and 'path' keys
    """
    files = []
    try:
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return files
        
        for py_file in path.rglob('*.py'):
            # Skip __pycache__ and virtual environments
            if '__pycache__' in str(py_file) or '.venv' in str(py_file) or 'env' in str(py_file):
                continue
            
            files.append({
                'name': py_file.name,
                'path': str(py_file.absolute()),
                'relative_path': str(py_file.relative_to(path))
            })
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
    
    return sorted(files, key=lambda x: x['relative_path'])


def node_to_dict(node: GNode) -> Dict[str, Any]:
    """Convert GNode to dictionary for JSON serialization."""
    return {
        'symbol': node.symbol,
        'type': node.type,
        'ctx': node.ctx,
        'start_byte': node.start_byte,
        'end_byte': node.end_byte,
        'children_count': len(node.children),
        'parent_count': len(node.parent) if node.parent else 0
    }


@app.route('/')
def index():
    """Serve the main debugger interface."""
    return render_template('index.html')


@app.route('/api/load_codebase', methods=['POST'])
def load_codebase():
    """Load and scan a codebase directory."""
    try:
        data = request.get_json()
        codebase_path = data.get('path', '')
        
        if not codebase_path:
            return jsonify({'error': 'Path is required', 'status': 'error'}), 400
        
        # Validate path
        path = Path(codebase_path)
        if not path.exists():
            return jsonify({'error': f'Path does not exist: {codebase_path}', 'status': 'error'}), 404
        
        if not path.is_dir():
            return jsonify({'error': f'Path is not a directory: {codebase_path}', 'status': 'error'}), 400
        
        # Scan for Python files
        files = scan_python_files(codebase_path)
        
        return jsonify({
            'files': files,
            'status': 'ok',
            'count': len(files)
        })
    
    except Exception as e:
        logger.error(f"Error loading codebase: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/load_file', methods=['POST'])
def load_file():
    """Load content of a file."""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({'error': 'file_path is required', 'status': 'error'}), 400
        
        path = Path(file_path)
        if not path.exists():
            return jsonify({'error': f'File does not exist: {file_path}', 'status': 'error'}), 404
        
        if not path.is_file():
            return jsonify({'error': f'Path is not a file: {file_path}', 'status': 'error'}), 400
        
        content = path.read_text(encoding='utf-8')
        
        return jsonify({
            'content': content,
            'status': 'ok',
            'file_path': file_path
        })
    
    except UnicodeDecodeError:
        return jsonify({'error': 'File is not UTF-8 encoded', 'status': 'error'}), 400
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/build_graph', methods=['POST'])
def build_graph():
    """Build stack graph for a file."""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        code = data.get('code', '')
        
        if not file_path and not code:
            return jsonify({'error': 'Either file_path or code is required', 'status': 'error'}), 400
        
        # Use code from request or load from file
        if code:
            file_content = code
        else:
            path = Path(file_path)
            if not path.exists():
                return jsonify({'error': f'File does not exist: {file_path}', 'status': 'error'}), 404
            file_content = path.read_text(encoding='utf-8')
        
        # Check cache (simple hash-based)
        code_hash = hash(file_content)
        cache_key = file_path or f"code_{code_hash}"
        
        if cache_key in graph_cache:
            cached_roots, cached_hash = graph_cache[cache_key]
            if cached_hash == code_hash:
                all_nodes = get_all_nodes(cached_roots)
                return jsonify({
                    'status': 'ok',
                    'node_count': len(all_nodes),
                    'cached': True
                })
        
        # Build graph
        builder = StackGraphBuilder(language='python')
        roots = builder.build_from_code(file_content)
        
        # Cache it
        graph_cache[cache_key] = (roots, code_hash)
        
        all_nodes = get_all_nodes(roots)
        
        return jsonify({
            'status': 'ok',
            'node_count': len(all_nodes),
            'cached': False
        })
    
    except Exception as e:
        logger.error(f"Error building graph: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/find_reference', methods=['POST'])
def find_reference():
    """Find a reference node at a specific position."""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        code = data.get('code', '')
        line = data.get('line', 0)
        column = data.get('column', 0)
        
        if not code:
            return jsonify({'error': 'code is required', 'status': 'error'}), 400
        
        if line < 1 or column < 1:
            return jsonify({'error': 'line and column must be >= 1', 'status': 'error'}), 400
        
        # Get or build graph
        code_hash = hash(code)
        cache_key = file_path or f"code_{code_hash}"
        
        if cache_key not in graph_cache:
            builder = StackGraphBuilder(language='python')
            roots = builder.build_from_code(code)
            graph_cache[cache_key] = (roots, code_hash)
        else:
            roots, _ = graph_cache[cache_key]
        
        # Find reference
        resolver = ReferenceResolver()
        ref_node = resolver.find_reference_by_position(roots, line, column, code)
        
        if ref_node is None:
            return jsonify({
                'reference': None,
                'status': 'ok',
                'message': 'No reference found at this position'
            })
        
        return jsonify({
            'reference': node_to_dict(ref_node),
            'status': 'ok'
        })
    
    except Exception as e:
        logger.error(f"Error finding reference: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/resolve', methods=['POST'])
def resolve():
    """Resolve a reference to its definition(s)."""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        code = data.get('code', '')
        line = data.get('line', 0)
        column = data.get('column', 0)
        
        if not code:
            return jsonify({'error': 'code is required', 'status': 'error'}), 400
        
        if line < 1 or column < 1:
            return jsonify({'error': 'line and column must be >= 1', 'status': 'error'}), 400
        
        # Get or build graph
        code_hash = hash(code)
        cache_key = file_path or f"code_{code_hash}"
        
        if cache_key not in graph_cache:
            builder = StackGraphBuilder(language='python')
            roots = builder.build_from_code(code)
            graph_cache[cache_key] = (roots, code_hash)
        else:
            roots, _ = graph_cache[cache_key]
        
        # Find reference
        resolver = ReferenceResolver()
        ref_node = resolver.find_reference_by_position(roots, line, column, code)
        
        if ref_node is None:
            return jsonify({
                'results': [],
                'status': 'ok',
                'message': 'No reference found at this position'
            })
        
        # Resolve
        results = resolver.resolve(ref_node, roots)
        
        # Convert results to dict
        results_dict = []
        for result in results:
            results_dict.append({
                'definition': node_to_dict(result.definition),
                'path': [node_to_dict(node) for node in result.path],
                'confidence': result.confidence
            })
        
        return jsonify({
            'results': results_dict,
            'status': 'ok',
            'reference': node_to_dict(ref_node)
        })
    
    except Exception as e:
        logger.error(f"Error resolving reference: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
