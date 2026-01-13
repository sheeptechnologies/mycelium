
import sys
import os
from dataclasses import asdict

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.graph_builder import StackGraphBuilder
from src.models import GNode

def dump_node(node: GNode, indent: int = 0):
    indent_str = "  " * indent
    # Basic info
    print(f"{indent_str}- Type: {node.type}")
    print(f"{indent_str}  Symbol: {node.symbol}")
    print(f"{indent_str}  Range: {node.start_byte}-{node.end_byte}")
    print(f"{indent_str}  Context: {node.ctx}")
    
    # You might want to print other attributes here if GNode evolves
    
    if node.children:
        print(f"{indent_str}  Children:")
        for child in node.children:
            dump_node(child, indent + 1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python runner.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    try:
        builder = StackGraphBuilder("python")
        roots = builder.build_from_file(file_path)
        
        print(f"--- STACK GRAPH FOR {os.path.basename(file_path)} ---")
        for root in roots:
            dump_node(root)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
