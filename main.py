from dataclasses import dataclass, field
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
from tree_sitter import Parser, Language, QueryCursor,Query
import tree_sitter_python as tspython

from src.visualizer import visualize_graph
from src.captures import CapturesManager
from src.graph import GraphBuilder

# Setup

# Code to parse
code = """  

full_name = lambda first, last: f'Full name: {first.title()} {last.title()}'
full_name('guido', 'van rossum')

"""


manager = CapturesManager("python")
parser = Parser(manager.LANGUAGE)
tree = parser.parse(code.encode("utf8"))


# 3. Esecuzione Query (Veloce)
sorted_captures = manager.execute(tree.root_node)
handler_map = manager.get_handlers()

print(tree.root_node)

# 4. Debug: Stampa le catture ordinate
for node, capture_name in sorted_captures:
    print(f"Capture: {capture_name} at {node.byte_range}")


builder_instance = GraphBuilder()   

roots = builder_instance.build(sorted_captures, handler_map)

visualize_graph(roots)