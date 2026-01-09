import os
import html
from typing import List
from .models import GNode

def visualize_graph(root_nodes: List[GNode], output_file: str = "graph.html"):
    """
    Generates an HTML file utilizing d3-graphviz (or viz.js) to visualize the graph using DOT language.
    """
    
    # We assign unique IDs for DOT nodes
    doc_id_map = {}
    next_id = 1
    visited = set()
    
    dot_lines = []
    edges = []

    def get_node_id(node: GNode):
        nonlocal next_id
        key = id(node)
        if key not in doc_id_map:
            doc_id_map[key] = f"node_{next_id}"
            next_id += 1
        return doc_id_map[key]

    def process_node(node: GNode, depth: int = 0):
        # Prevent cycles / infinite recursion
        if id(node) in visited:
            return

        # OWNERSHIP LOGIC:
        if node.parent:
             pass
        
        visited.add(id(node))

        my_id = get_node_id(node)
        
        # Safe label for DOT (escape quotes)
        label = node.symbol.replace('"', '\\"')
        
        node_type = node.type.strip()
        
        if node_type == 'SCOPE':
            # SCOPE -> subgraph cluster
            cluster_name = f"cluster_{my_id}"
            
            # Refined Depth-based styling: Softer, more "material" darks
            # Base is #1e1e1e. Layers:
            bg_colors = ["#252526", "#2d2d30", "#333333", "#3e3e42"]
            fill_color = bg_colors[depth % len(bg_colors)]
            
            # Start subgraph
            dot_lines.append(f'subgraph {cluster_name} {{')
            dot_lines.append(f'    fillcolor="{fill_color}";')
            dot_lines.append('    style="filled,rounded";')
            dot_lines.append('    color="#555555";') # Subtle border
            dot_lines.append('    penwidth=1.0;') 
            dot_lines.append('    margin=24;') # Spacious
            
            dot_lines.append('    node [style="filled,rounded", fontname="Fira Code, monospace", fontsize=10];')
            
            # Scope Node (The "Header" Node)
            # Distinct "Pill" style
            # Blue accent for header: #0984e3 (Prunus Avium?) No, let's go with a nice VSCode Blue: #007acc
            dot_lines.append(f'    "{my_id}" [label="{label}", shape=rect, style="filled,rounded", color="#007acc", fillcolor="#007acc", fontcolor="white", fontsize=12, penwidth=0, margin="0.2,0.1"];')

            # Recurse children inside the subgraph
            for child in node.children:
                if not child.parent or id(child.parent[0]) == id(node):
                    process_node(child, depth + 1)
            
            dot_lines.append('}')

        else:
            # LEAF / STRUCTURAL NODES
            shape = "box"
            style = "filled,rounded"
            color = "#444444" # Subtle border
            fillcolor = "#383838" # Card-like grey
            fontcolor = "#ecf0f1"
            
            if node_type == 'PUSH':
                label = f"{label} ↓"
                fillcolor = "#4e342e" # Muted Red background
                color = "#ff5252" # Bright Red border/text accent
                fontcolor = "#ff5252"
                style = "filled,rounded,bold"
            elif node_type == 'POP':
                label = f"{label} ↑"
                fillcolor = "#1b3a2f" # Muted Green background
                color = "#00b894" # Bright Green border/text accent
                fontcolor = "#00b894"
                style = "filled,rounded,bold"
            
            # Normal nodes: #383838 background, #ecf0f1 text
            dot_lines.append(f'    "{my_id}" [label="{label}", shape="{shape}", style="{style}", color="{color}", fillcolor="{fillcolor}", fontcolor="{fontcolor}", penwidth=1.0];')

            # Recurse children
            for child in node.children:
                 if not child.parent or id(child.parent[0]) == id(node):
                    process_node(child, depth + 1)

        # Process Edges
        for child in node.children:
            child_id = get_node_id(child)
            
            attrs = []
            if child.type.strip() == 'SCOPE':
                attrs.append(f'lhead="cluster_{child_id}"')
            
            # Edge styling: Subtle grey curves
            attrs.append('color="#666666"') 
            attrs.append('penwidth=0.8')
            attrs.append('arrowsize=0.6')
            
            attr_str = ""
            if attrs:
                attr_str = f" [{', '.join(attrs)}]"

            edges.append(f'    "{my_id}" -> "{child_id}"{attr_str};')

    # Start DOT
    dot_lines.append('digraph G {')
    dot_lines.append('    compound=true;') # Allow edges to clusters
    dot_lines.append('    rankdir=TB;') # Top to Bottom
    dot_lines.append('    bgcolor="#222f3e";') # Graph Background
    dot_lines.append('    node [fontname="Helvetica,Arial,sans-serif"];')
    dot_lines.append('    edge [fontname="Helvetica,Arial,sans-serif"];')
    # Splines ortho or polyline for cleaner edges? Or splines=spline (default)
    dot_lines.append('    splines=polyline;') 
    dot_lines.append('    nodesep=0.6;')
    dot_lines.append('    ranksep=0.8;')
    dot_lines.append('    clusterrank=local;') # Keep clusters tight

    for root in root_nodes:
        process_node(root)
    
    # Add accumulated edges
    dot_lines.extend(edges)
    
    dot_lines.append('}')
    
    dot_source = "\n".join(dot_lines)
    
    # Escape for JS string
    # We use a trick: <script type="text/vnd.graphviz" id="graph"> ... </script>
    # and read it. safer than escaping string literals.
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Graph Visualization (DOT)</title>
    <script src="https://unpkg.com/viz.js@2.1.2/viz.js"></script>
    <script src="https://unpkg.com/viz.js@2.1.2/full.render.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #222; color: #eee; }}
        #graph {{ width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; }}
        svg {{ width: 100%; height: 100%; }}
    </style>
</head>
<body>
    <div id="graph"></div>
    
    <!-- data island -->
    <script type="text/vnd.graphviz" id="dot-source">
{dot_source}
    </script>

    <script>
        var viz = new Viz();
        var dotSource = document.getElementById('dot-source').innerText;
        
        viz.renderSVGElement(dotSource)
        .then(function(element) {{
            document.getElementById('graph').appendChild(element);
        }})
        .catch(error => {{
            // Create a new Viz instance (sometimes helps with state) to render error
            console.error(error);
            document.getElementById('graph').innerHTML = "<div style='color:red; font-family:monospace'><pre>Rendering Error: " + error + "</pre></div>";
        }});
    </script>
</body>
</html>
"""

    with open(output_file, "w") as f:
        f.write(html_content)
    
    print(f"Graph visualization saved to {os.path.abspath(output_file)}")
