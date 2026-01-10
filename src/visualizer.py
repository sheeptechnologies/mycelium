import os
import html
import json
from typing import List, Optional, Dict, Any
from .models import GNode

def visualize_graph(root_nodes: List[GNode], output_file: str = "graph.html", title: Optional[str] = None):
    """
    Generates an interactive HTML file using D3.js to visualize the graph.
    Initially shows only root nodes and top-level scopes. Click on a scope to expand/collapse it.
    
    Args:
        root_nodes: List of root GNode objects representing the stack graph
        output_file: Path to output HTML file
        title: Optional title for the visualization
    """
    
    # Build graph structure as JSON
    node_id_map = {}
    next_id = 0
    visited = set()
    
    stats = {
        'total_nodes': 0,
        'scope_nodes': 0,
        'push_nodes': 0,
        'pop_nodes': 0,
        'other_nodes': 0
    }
    
    def get_node_id(node: GNode):
        nonlocal next_id
        key = id(node)
        if key not in node_id_map:
            node_id_map[key] = next_id
            next_id += 1
        return node_id_map[key]
    
    # Build complete graph structure
    all_nodes = {}
    root_ids = []
    
    def collect_all_nodes(node: GNode, depth: int = 0):
        """Recursively collect all nodes."""
        if id(node) in visited:
            return
        visited.add(id(node))
        
        # Build node data
        stats['total_nodes'] += 1
        node_id = get_node_id(node)
        node_type = node.type.strip()
        
        if node_type == 'SCOPE':
            stats['scope_nodes'] += 1
        elif node_type == 'PUSH':
            stats['push_nodes'] += 1
        elif node_type == 'POP':
            stats['pop_nodes'] += 1
        else:
            stats['other_nodes'] += 1
        
        # Build children list (only direct children, not recursive)
        children_data = []
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                # Only include direct children (avoid cycles)
                # Check if this node is the parent of the child
                is_direct_child = False
                if hasattr(child, 'parent') and child.parent and len(child.parent) > 0:
                    # Check if any parent matches this node
                    for parent in child.parent:
                        if id(parent) == id(node):
                            is_direct_child = True
                            break
                else:
                    # If child has no parent list or empty parent list, 
                    # include it as a direct child (simpler approach)
                    is_direct_child = True
                
                if is_direct_child:
                    child_id = get_node_id(child)
                    children_data.append(child_id)
        
        node_data = {
            'id': node_id,
            'symbol': node.symbol,
            'type': node_type,
            'ctx': getattr(node, 'ctx', ''),
            'start_byte': getattr(node, 'start_byte', 0),
            'end_byte': getattr(node, 'end_byte', 0),
            'children': children_data,
            'depth': depth,
            'expanded': False  # Initially collapsed
        }
        
        all_nodes[node_id] = node_data
        
        # Recursively collect children
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                # Check if this node is the parent of the child
                is_direct_child = False
                if hasattr(child, 'parent') and child.parent and len(child.parent) > 0:
                    for parent in child.parent:
                        if id(parent) == id(node):
                            is_direct_child = True
                            break
                else:
                    # Include if no parent defined
                    is_direct_child = True
                
                if is_direct_child:
                    collect_all_nodes(child, depth + 1)
    
    # Reset visited for collection
    visited.clear()
    for root in root_nodes:
        if root:  # Check if root is not None
            root_id = get_node_id(root)
            root_ids.append(root_id)
            collect_all_nodes(root, 0)
    
    # Build edges
    edges = []
    for node_data in all_nodes.values():
        for child_id in node_data['children']:
            if child_id in all_nodes:
                edges.append({
                    'source': node_data['id'],
                    'target': child_id
                })
    
    graph_data = {
        'nodes': list(all_nodes.values()),
        'edges': edges,
        'roots': root_ids
    }
    
    graph_title = title or "Stack Graph Visualization"
    
    # Debug: Check if we have any nodes
    if len(all_nodes) == 0:
        print("WARNING: No nodes found in graph! Root nodes count:", len(root_nodes))
        if root_nodes:
            print("First root node type:", type(root_nodes[0]))
            print("First root node symbol:", getattr(root_nodes[0], 'symbol', 'N/A'))
            print("First root node has children:", hasattr(root_nodes[0], 'children'))
            if hasattr(root_nodes[0], 'children'):
                print("First root node children count:", len(root_nodes[0].children))
                if len(root_nodes[0].children) > 0:
                    print("First child type:", type(root_nodes[0].children[0]))
                    print("First child symbol:", getattr(root_nodes[0].children[0], 'symbol', 'N/A'))
    else:
        print(f"DEBUG: Collected {len(all_nodes)} nodes, {len(edges)} edges, {len(root_ids)} roots")
    
    # Escape JSON for embedding in HTML
    try:
        graph_json = json.dumps(graph_data, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to serialize graph data: {e}")
        # Create minimal valid graph
        graph_data = {
            'nodes': [],
            'edges': [],
            'roots': []
        }
        graph_json = json.dumps(graph_data, indent=2)
    
    stats_html = f"""
    <div id="stats-panel" style="position: fixed; top: 10px; right: 10px; background: rgba(30, 30, 30, 0.95); padding: 15px; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 12px; color: #eee; z-index: 1000; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <strong style="color: #007acc; font-size: 14px;">Graph Statistics</strong><br>
        <hr style="border-color: #444; margin: 8px 0;">
        Total Nodes: <span style="color: #fff;">{stats['total_nodes']}</span><br>
        <span style="color: #007acc;">SCOPE:</span> <span style="color: #fff;">{stats['scope_nodes']}</span><br>
        <span style="color: #42a5f5;">PUSH (Ref):</span> <span style="color: #fff;">{stats['push_nodes']}</span><br>
        <span style="color: #66bb6a;">POP (Def):</span> <span style="color: #fff;">{stats['pop_nodes']}</span><br>
        <span style="color: #9e9e9e;">Other:</span> <span style="color: #fff;">{stats['other_nodes']}</span><br>
        <hr style="border-color: #444; margin: 8px 0;">
        <div style="font-size: 10px; color: #999; margin-top: 8px;">
            Click on SCOPE nodes to expand/collapse
        </div>
    </div>
    """
    
    legend_html = """
    <div id="legend-panel" style="position: fixed; top: 10px; left: 10px; background: rgba(30, 30, 30, 0.95); padding: 15px; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 12px; color: #eee; z-index: 1000; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3); max-width: 250px;">
        <strong style="color: #007acc; font-size: 14px;">Legend</strong><br>
        <hr style="border-color: #444; margin: 8px 0;">
        <div style="margin: 5px 0;">
            <span style="display: inline-block; width: 20px; height: 20px; background: #007acc; border-radius: 3px; vertical-align: middle; margin-right: 8px;"></span>
            <span>SCOPE (Click to expand)</span>
        </div>
        <div style="margin: 5px 0;">
            <span style="display: inline-block; width: 20px; height: 20px; background: #1565c0; border: 2px solid #64b5f6; border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span>PUSH (Reference)</span>
        </div>
        <div style="margin: 5px 0;">
            <span style="display: inline-block; width: 20px; height: 20px; background: #2e7d32; border: 2px solid #81c784; vertical-align: middle; margin-right: 8px;"></span>
            <span>POP (Definition)</span>
        </div>
        <hr style="border-color: #444; margin: 8px 0;">
        <div style="font-size: 10px; color: #999; margin-top: 8px;">
            Hover for details | Click SCOPE to expand
        </div>
    </div>
    """
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html.escape(graph_title)}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #1e1e1e;
            color: #eee;
            font-family: 'Fira Code', 'Consolas', monospace;
        }}
        #graph-container {{
            width: 100vw;
            height: 100vh;
            overflow: auto;
        }}
        svg {{
            background: #1e1e1e;
        }}
        .node {{
            cursor: pointer;
        }}
        .node.scope {{
            cursor: pointer;
        }}
        .node.scope:hover {{
            opacity: 0.8;
        }}
        .node-label {{
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 11px;
            pointer-events: none;
            fill: #fff;
        }}
        .node.scope .node-label {{
            font-weight: bold;
            font-size: 12px;
            fill: #fff;
        }}
        .link {{
            fill: none;
            stroke: #666;
            stroke-width: 1.5px;
        }}
        .link.scope-link {{
            stroke: #007acc;
            stroke-width: 2px;
        }}
        .link.push-link {{
            stroke: #42a5f5;
        }}
        .link.pop-link {{
            stroke: #66bb6a;
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            color: #eee;
            z-index: 1000;
        }}
        .controls button {{
            background: #007acc;
            color: white;
            border: none;
            padding: 5px 10px;
            margin: 5px;
            border-radius: 3px;
            cursor: pointer;
        }}
        .controls button:hover {{
            background: #005a9e;
        }}
        .expand-indicator {{
            font-size: 10px;
            fill: #007acc;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    {legend_html}
    {stats_html}
    <div id="graph-container"></div>
    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button onclick="resetView()">Reset View</button>
    </div>
    
    <script>
        const graphData = {graph_json};
        
        // Node and link arrays for D3
        let nodes = [];
        let links = [];
        let visibleNodes = new Set();
        let visibleLinks = new Set();
        
        // Initialize: only show root nodes and top-level scopes
        function initializeGraph() {{
            nodes = graphData.nodes.map(n => ({{
                ...n,
                x: 0,
                y: 0,
                visible: false,
                expanded: false
            }}));
            
            links = graphData.edges.map(e => ({{
                ...e,
                visible: false
            }}));
            
            // Mark root nodes and their immediate children as visible
            graphData.roots.forEach(rootId => {{
                setNodeVisible(rootId, true);
                const node = nodes.find(n => n.id === rootId);
                if (node && node.type === 'SCOPE') {{
                    // Show immediate children of root scopes
                    node.children.forEach(childId => {{
                        setNodeVisible(childId, true);
                    }});
                }}
            }});
        }}
        
        function setNodeVisible(nodeId, visible) {{
            const node = nodes.find(n => n.id === nodeId);
            if (!node) return;
            
            node.visible = visible;
            if (visible) {{
                visibleNodes.add(nodeId);
            }} else {{
                visibleNodes.delete(nodeId);
            }}
            
            // Update links visibility
            links.forEach(link => {{
                if (link.source === nodeId || link.target === nodeId) {{
                    const sourceVisible = visibleNodes.has(link.source);
                    const targetVisible = visibleNodes.has(link.target);
                    link.visible = sourceVisible && targetVisible;
                    
                    if (link.visible) {{
                        visibleLinks.add(link);
                    }} else {{
                        visibleLinks.delete(link);
                    }}
                }}
            }});
        }}
        
        function toggleNode(nodeId) {{
            const node = nodes.find(n => n.id === nodeId);
            if (!node || node.type !== 'SCOPE') return;
            
            node.expanded = !node.expanded;
            
            if (node.expanded) {{
                // Expand: show children
                node.children.forEach(childId => {{
                    setNodeVisible(childId, true);
                    // Recursively show children if they are expanded scopes
                    const child = nodes.find(n => n.id === childId);
                    if (child && child.type === 'SCOPE' && child.expanded) {{
                        child.children.forEach(grandchildId => {{
                            setNodeVisible(grandchildId, true);
                        }});
                    }}
                }});
            }} else {{
                // Collapse: hide children recursively
                function hideChildren(parentId) {{
                    const parent = nodes.find(n => n.id === parentId);
                    if (!parent) return;
                    
                    parent.children.forEach(childId => {{
                        setNodeVisible(childId, false);
                        hideChildren(childId);
                    }});
                }}
                hideChildren(nodeId);
            }}
            
            updateGraph();
        }}
        
        function expandAll() {{
            nodes.forEach(node => {{
                if (node.type === 'SCOPE') {{
                    node.expanded = true;
                    setNodeVisible(node.id, true);
                    node.children.forEach(childId => {{
                        setNodeVisible(childId, true);
                    }});
                }}
            }});
            updateGraph();
        }}
        
        function collapseAll() {{
            nodes.forEach(node => {{
                if (node.type === 'SCOPE') {{
                    node.expanded = false;
                }}
            }});
            initializeGraph();
            updateGraph();
        }}
        
        function resetView() {{
            const transform = d3.zoomIdentity;
            svg.call(zoom.transform, transform);
        }}
        
        // D3 setup
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Pan with mouse drag
        let isPanning = false;
        svg.on("mousedown", function(event) {{
            if (event.button === 1 || (event.button === 0 && (event.ctrlKey || event.metaKey))) {{
                isPanning = true;
                svg.style("cursor", "grabbing");
            }}
        }});
        
        svg.on("mousemove", function(event) {{
            if (isPanning) {{
                const transform = d3.zoomTransform(svg.node());
                const newTransform = transform.translate(
                    event.movementX / transform.k,
                    event.movementY / transform.k
                );
                svg.call(zoom.transform, d3.zoomIdentity.scale(transform.k).translate(newTransform.x, newTransform.y));
            }}
        }});
        
        svg.on("mouseup", function() {{
            isPanning = false;
            svg.style("cursor", "default");
        }});
        
        // Prevent context menu
        svg.on("contextmenu", function(event) {{
            event.preventDefault();
        }});
        
        function updateGraph() {{
            const visibleNodesList = nodes.filter(n => n.visible);
            const visibleLinksList = links.filter(l => l.visible);
            
            // Convert link source/target IDs to node references for D3
            const linksForSimulation = visibleLinksList.map(link => {{
                const sourceNode = nodes.find(n => n.id === link.source);
                const targetNode = nodes.find(n => n.id === link.target);
                return {{
                    source: sourceNode,
                    target: targetNode,
                    original: link
                }};
            }}).filter(link => link.source && link.target);
            
            // Use force simulation for layout
            const simulation = d3.forceSimulation(visibleNodesList)
                .force("link", d3.forceLink(linksForSimulation).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(30));
            
            currentSimulation = simulation;
            
            // Update links
            let link = g.selectAll(".link")
                .data(linksForSimulation, d => d.source.id + "-" + d.target.id);
            
            link.exit().remove();
            
            const linkEnter = link.enter()
                .append("line")
                .attr("class", d => {{
                    const sourceNode = d.source;
                    return "link " + (sourceNode ? sourceNode.type.toLowerCase() + "-link" : "");
                }});
            
            link = linkEnter.merge(link);
            
            // Update nodes
            let node = g.selectAll(".node")
                .data(visibleNodesList, d => d.id);
            
            node.exit().remove();
            
            const nodeEnter = node.enter()
                .append("g")
                .attr("class", d => "node " + d.type.toLowerCase())
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Add circles for nodes
            nodeEnter.append("circle")
                .attr("r", d => {{
                    if (d.type === 'SCOPE') return 25;
                    if (d.type === 'PUSH') return 15;
                    if (d.type === 'POP') return 18;
                    return 12;
                }})
                .attr("fill", d => {{
                    if (d.type === 'SCOPE') return "#007acc";
                    if (d.type === 'PUSH') return "#1565c0";
                    if (d.type === 'POP') return "#2e7d32";
                    return "#666";
                }})
                .attr("stroke", d => {{
                    if (d.type === 'SCOPE') return "#007acc";
                    if (d.type === 'PUSH') return "#64b5f6";
                    if (d.type === 'POP') return "#81c784";
                    return "#999";
                }})
                .attr("stroke-width", 2);
            
            // Add expand indicator for scopes
            nodeEnter.filter(d => d.type === 'SCOPE')
                .append("text")
                .attr("class", "expand-indicator")
                .attr("text-anchor", "middle")
                .attr("dy", -30)
                .text(d => d.expanded ? "−" : "+");
            
            // Add labels
            nodeEnter.append("text")
                .attr("class", "node-label")
                .attr("text-anchor", "middle")
                .attr("dy", d => {{
                    if (d.type === 'SCOPE') return 5;
                    return 4;
                }})
                .text(d => {{
                    const symbol = d.symbol;
                    if (symbol.length > 15) return symbol.substring(0, 12) + "...";
                    return symbol;
                }});
            
            node = nodeEnter.merge(node);
            
            // Add click handler for scopes
            node.filter(d => d.type === 'SCOPE')
                .on("click", function(event, d) {{
                    event.stopPropagation();
                    toggleNode(d.id);
                }});
            
            // Add tooltips
            node.append("title")
                .text(d => {{
                    let tooltip = d.symbol + "\\nType: " + d.type;
                    if (d.ctx) tooltip += "\\nContext: " + d.ctx;
                    if (d.type === 'SCOPE') {{
                        tooltip += "\\nChildren: " + d.children.length;
                        tooltip += "\\nClick to " + (d.expanded ? "collapse" : "expand");
                    }}
                    return tooltip;
                }});
            
            // Update positions on simulation tick
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});
        }}
        
        let currentSimulation = null;
        
        function dragstarted(event, d) {{
            if (!event.active && currentSimulation) currentSimulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active && currentSimulation) currentSimulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Initialize and render
        initializeGraph();
        updateGraph();
    </script>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    abs_path = os.path.abspath(output_file)
    print(f"Interactive graph visualization saved to {abs_path}")
    print(f"Statistics: {stats['total_nodes']} nodes ({stats['scope_nodes']} SCOPE, {stats['push_nodes']} PUSH, {stats['pop_nodes']} POP)")
    print("Note: Graph is initially collapsed. Click on SCOPE nodes to expand them.")
    return abs_path
