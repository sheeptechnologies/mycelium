import os
import html
import json
from typing import List, Optional, Dict, Any
from .models import GNode

def visualize_graph(
    root_nodes: List[GNode],
    output_file: str = "graph.html",
    title: Optional[str] = None,
    source_code: Optional[str] = None,
    source_path: Optional[str] = None,
):
    """
    Generates an interactive HTML file using D3.js to visualize the graph.
    Renders a static full graph view with search and filtering for readability.
    Optionally embeds source code for side-by-side inspection.
    
    Args:
        root_nodes: List of root GNode objects representing the stack graph
        output_file: Path to output HTML file
        title: Optional title for the visualization
        source_code: Optional source code string to embed in the view
        source_path: Optional source path label for the code panel
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
            'depth': depth
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

    source_code = source_code or ""
    source_path = source_path or ""
    source_json = json.dumps(source_code)
    source_path_json = json.dumps(source_path)
    
    stats_html = f"""
    <div id="stats-panel" style="position: absolute; top: 10px; right: 10px; background: rgba(30, 30, 30, 0.95); padding: 15px; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 12px; color: #eee; z-index: 1000; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <strong style="color: #007acc; font-size: 14px;">Graph Statistics</strong><br>
        <hr style="border-color: #444; margin: 8px 0;">
        Total Nodes: <span style="color: #fff;">{stats['total_nodes']}</span><br>
        <span style="color: #007acc;">SCOPE:</span> <span style="color: #fff;">{stats['scope_nodes']}</span><br>
        <span style="color: #42a5f5;">PUSH (Ref):</span> <span style="color: #fff;">{stats['push_nodes']}</span><br>
        <span style="color: #66bb6a;">POP (Def):</span> <span style="color: #fff;">{stats['pop_nodes']}</span><br>
        <span style="color: #9e9e9e;">Other:</span> <span style="color: #fff;">{stats['other_nodes']}</span><br>
        <hr style="border-color: #444; margin: 8px 0;">
        <div style="font-size: 10px; color: #999; margin-top: 8px;">
            Click a node to highlight code
        </div>
    </div>
    """
    
    legend_html = """
    <div id="legend-panel" style="position: absolute; top: 10px; left: 10px; background: rgba(30, 30, 30, 0.95); padding: 15px; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 12px; color: #eee; z-index: 1000; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3); max-width: 250px;">
        <strong style="color: #007acc; font-size: 14px;">Legend</strong><br>
        <hr style="border-color: #444; margin: 8px 0;">
        <div style="margin: 5px 0;">
            <span style="display: inline-block; width: 20px; height: 20px; background: #007acc; border-radius: 3px; vertical-align: middle; margin-right: 8px;"></span>
            <span>SCOPE</span>
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
            Hover for details | Click a node to highlight code
        </div>
    </div>
    """

    inspector_html = """
    <div id="inspector-panel">
        <div class="panel-title">Inspector</div>
        <div class="panel-section">
            <label class="panel-label">Search</label>
            <input id="search-input" type="text" placeholder="symbol or ctx">
            <div class="panel-row">
                <label><input type="checkbox" id="filter-scope" checked> SCOPE</label>
                <label><input type="checkbox" id="filter-push" checked> PUSH</label>
            </div>
            <div class="panel-row">
                <label><input type="checkbox" id="filter-pop" checked> POP</label>
                <label><input type="checkbox" id="filter-other" checked> OTHER</label>
            </div>
        </div>
        <div class="panel-section">
            <label class="panel-label">Node List</label>
            <div id="node-count" class="small"></div>
            <div id="node-list"></div>
        </div>
    </div>
    <div id="detail-panel">
        <div class="panel-title">Details</div>
        <div id="detail-content" class="small">Click a node</div>
        <div class="panel-actions">
            <button id="center-node-btn">Center</button>
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
            background: #0f0f0f;
            color: #eee;
            font-family: 'Fira Code', 'Consolas', monospace;
            height: 100vh;
        }}
        #layout {{
            display: grid;
            grid-template-columns: 45% 55%;
            height: 100vh;
            width: 100vw;
        }}
        #code-panel {{
            background: #0f0f0f;
            border-right: 1px solid #333;
            padding: 12px;
            overflow: auto;
        }}
        #code-view {{
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
        }}
        .code-line {{
            display: flex;
            gap: 12px;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .code-line:hover {{
            background: #1c1c1c;
        }}
        .code-line.selected {{
            background: #2b4a6d;
        }}
        .line-no {{
            color: #666;
            min-width: 42px;
            text-align: right;
            user-select: none;
        }}
        .line-text {{
            color: #ddd;
            white-space: pre;
        }}
        #graph-panel {{
            position: relative;
            background: #1e1e1e;
            overflow: hidden;
        }}
        #inspector-panel {{
            position: absolute;
            top: 180px;
            left: 10px;
            width: 280px;
            max-height: calc(100% - 200px);
            overflow: auto;
            background: rgba(20, 20, 20, 0.95);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        }}
        #detail-panel {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            width: 320px;
            background: rgba(20, 20, 20, 0.95);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        }}
        .panel-title {{
            font-size: 13px;
            font-weight: bold;
            color: #8ab4f8;
            margin-bottom: 8px;
        }}
        .panel-section {{
            margin-bottom: 12px;
        }}
        .panel-label {{
            display: block;
            font-size: 11px;
            color: #bbb;
            margin-bottom: 6px;
        }}
        .panel-row {{
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 6px;
            flex-wrap: wrap;
        }}
        .panel-row.small {{
            font-size: 11px;
            color: #aaa;
        }}
        #search-input {{
            width: 100%;
            padding: 6px 8px;
            border-radius: 4px;
            border: 1px solid #444;
            background: #111;
            color: #eee;
        }}
        #node-list {{
            max-height: 240px;
            overflow: auto;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 6px;
            background: #151515;
        }}
        #detail-content {{
            white-space: pre-wrap;
        }}
        .node-item {{
            padding: 4px 6px;
            margin-bottom: 2px;
            cursor: pointer;
            border-radius: 3px;
        }}
        .node-item:hover {{
            background: #222;
        }}
        .node-item.selected {{
            background: #2b4a6d;
        }}
        .panel-actions button {{
            background: #007acc;
            color: white;
            border: none;
            padding: 4px 8px;
            margin-right: 6px;
            border-radius: 3px;
            cursor: pointer;
        }}
        .panel-actions button:hover {{
            background: #005a9e;
        }}
        .small {{
            font-size: 11px;
            color: #bbb;
        }}
        #graph-container {{
            width: 100%;
            height: 100%;
            overflow: auto;
        }}
        svg {{
            background: #1e1e1e;
            display: block;
        }}
        .node {{
            cursor: pointer;
        }}
        .node.selected circle {{
            stroke: #ffb300;
            stroke-width: 4px;
        }}
        .node.match circle {{
            stroke: #fdd835;
            stroke-width: 3px;
        }}
        .node.dim {{
            opacity: 0.2;
        }}
        .node.hidden {{
            display: none;
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
        .link.highlight {{
            stroke: #ffb300;
            stroke-width: 3px;
        }}
        .link.dim {{
            opacity: 0.15;
        }}
        .link.hidden {{
            display: none;
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
    </style>
</head>
<body>
    <div id="layout">
        <div id="code-panel">
            <div class="panel-title">Source</div>
            <div id="code-meta" class="small"></div>
            <div id="code-view"></div>
        </div>
        <div id="graph-panel">
            {legend_html}
            {stats_html}
            {inspector_html}
            <div id="graph-container"></div>
        </div>
    </div>
    <script>
        const graphData = {graph_json};
        const sourceCode = {source_json};
        const sourcePath = {source_path_json};
        const graphPanel = document.getElementById("graph-panel");
        const graphContainer = document.getElementById("graph-container");
        const parentIdsByNode = new Map();
        graphData.edges.forEach(edge => {{
            if (!parentIdsByNode.has(edge.target)) {{
                parentIdsByNode.set(edge.target, []);
            }}
            parentIdsByNode.get(edge.target).push(edge.source);
        }});
        
        // Node and link arrays for D3
        let nodes = [];
        let links = [];
        let nodeById = new Map();
        let selectedNodeId = null;
        let matchIds = new Set();
        let filters = {{
            SCOPE: true,
            PUSH: true,
            POP: true,
            OTHER: true
        }};
        let nodeSelection = null;
        let linkSelection = null;
        let codeLineMeta = [];
        let codeLineElements = [];
        let graphWidth = 0;
        let graphHeight = 0;
        let svg = null;
        let g = null;
        
        // Initialize: load all nodes and edges
        function initializeGraph() {{
            nodes = graphData.nodes.map(n => {{
                const depth = Number.isFinite(n.depth) ? n.depth : 0;
                return {{ ...n, depth }};
            }});
            nodeById = new Map(nodes.map(n => [n.id, n]));
            links = graphData.edges.map(e => ({{
                source: nodeById.get(e.source),
                target: nodeById.get(e.target)
            }})).filter(link => link.source && link.target);
        }}

        function nodeMatchesFilter(node) {{
            if (node.type === 'SCOPE') return filters.SCOPE;
            if (node.type === 'PUSH') return filters.PUSH;
            if (node.type === 'POP') return filters.POP;
            return filters.OTHER;
        }}

        function applySearch(term) {{
            const lowerTerm = term.trim().toLowerCase();
            matchIds.clear();
            if (!lowerTerm) {{
                updateNodeList();
                updateGraphStyles();
                return;
            }}

            nodes.forEach(node => {{
                const sym = (node.symbol || '').toLowerCase();
                const ctx = (node.ctx || '').toLowerCase();
                if (sym.includes(lowerTerm) || ctx.includes(lowerTerm)) {{
                    matchIds.add(node.id);
                }}
            }});
            updateNodeList();
            updateGraphStyles();
        }}

        function updateNodeList() {{
            const list = document.getElementById("node-list");
            const count = document.getElementById("node-count");
            if (!list || !count) return;

            const filtered = nodes.filter(n => nodeMatchesFilter(n));
            const listed = matchIds.size === 0 ? filtered : filtered.filter(n => matchIds.has(n.id));
            const totalText = matchIds.size === 0
                ? `${{listed.length}} nodes`
                : `${{listed.length}} of ${{filtered.length}} nodes`;
            count.textContent = totalText;

            list.innerHTML = "";
            listed.slice(0, 500).forEach(node => {{
                const item = document.createElement("div");
                item.className = "node-item" + (node.id === selectedNodeId ? " selected" : "");
                item.textContent = `${{node.symbol}} (${{node.type}})`;
                item.onclick = () => {{
                    selectNode(node);
                }};
                list.appendChild(item);
            }});
        }}

        function buildCodeView() {{
            const codeView = document.getElementById("code-view");
            const codeMeta = document.getElementById("code-meta");
            if (!codeView) return;

            if (codeMeta) {{
                codeMeta.textContent = sourcePath || "Source";
            }}

            if (!sourceCode) {{
                codeView.textContent = "No source provided.";
                return;
            }}

            const encoder = new TextEncoder();
            const lines = sourceCode.split("\\n");
            let byteOffset = 0;
            codeLineMeta = [];
            codeLineElements = [];
            codeView.innerHTML = "";

            lines.forEach((line, index) => {{
                const lineBytes = encoder.encode(line);
                const start = byteOffset;
                const end = start + lineBytes.length;
                byteOffset = end + (index < lines.length - 1 ? 1 : 0);
                codeLineMeta.push({{ start, end }});

                const lineEl = document.createElement("div");
                lineEl.className = "code-line";
                lineEl.dataset.line = String(index + 1);
                lineEl.dataset.start = String(start);
                lineEl.dataset.end = String(end);

                const numberEl = document.createElement("span");
                numberEl.className = "line-no";
                numberEl.textContent = String(index + 1);

                const textEl = document.createElement("span");
                textEl.className = "line-text";
                textEl.textContent = line === "" ? " " : line;

                lineEl.append(numberEl, textEl);
                lineEl.addEventListener("click", () => {{
                    selectNodeFromLine(index);
                }});

                codeView.appendChild(lineEl);
                codeLineElements.push(lineEl);
            }});
        }}

        function findLineForByte(byteOffset) {{
            if (!codeLineMeta.length) return null;
            for (let i = 0; i < codeLineMeta.length; i++) {{
                const meta = codeLineMeta[i];
                if (byteOffset <= meta.end) {{
                    return i;
                }}
            }}
            return codeLineMeta.length - 1;
        }}

        function highlightCodeForNode(node) {{
            if (!codeLineElements.length) return;
            codeLineElements.forEach(el => el.classList.remove("selected"));
            if (!node) return;

            let firstIndex = null;
            for (let i = 0; i < codeLineMeta.length; i++) {{
                const meta = codeLineMeta[i];
                const overlaps = meta.start <= node.end_byte && meta.end >= node.start_byte;
                if (overlaps) {{
                    codeLineElements[i].classList.add("selected");
                    if (firstIndex === null) firstIndex = i;
                }}
            }}

            if (firstIndex !== null) {{
                codeLineElements[firstIndex].scrollIntoView({{ block: "center" }});
            }}
        }}

        function selectNodeFromLine(lineIndex) {{
            if (!codeLineMeta.length) return;
            const meta = codeLineMeta[lineIndex];
            if (!meta) return;
            const candidates = nodes.filter(n => n.start_byte <= meta.end && n.end_byte >= meta.start);
            if (candidates.length === 0) return;

            let best = candidates[0];
            candidates.forEach(candidate => {{
                const size = candidate.end_byte - candidate.start_byte;
                const bestSize = best.end_byte - best.start_byte;
                if (size < bestSize) {{
                    best = candidate;
                }}
            }});

            selectNode(best);
            centerOnNode(best);
        }}

        function getParents(nodeId) {{
            const parentIds = parentIdsByNode.get(nodeId) || [];
            return parentIds.map(pid => nodeById.get(pid)).filter(Boolean);
        }}

        function renderDetails(node) {{
            const detail = document.getElementById("detail-content");
            if (!detail || !node) return;
            const parents = getParents(node.id);
            const parentSymbols = parents.map(p => p.symbol).join(", ");
            const childSymbols = node.children.map(cid => nodeById.get(cid)).filter(Boolean).map(c => c.symbol).join(", ");
            const startLine = findLineForByte(node.start_byte);
            const endLine = findLineForByte(node.end_byte);
            const lineInfo = startLine === null ? "N/A" : `${{startLine + 1}}-${{(endLine ?? startLine) + 1}}`;
            detail.textContent =
                `symbol: ${{node.symbol}}\n` +
                `type: ${{node.type}}\n` +
                `ctx: ${{node.ctx}}\n` +
                `start_byte: ${{node.start_byte}}\n` +
                `end_byte: ${{node.end_byte}}\n` +
                `lines: ${{lineInfo}}\n` +
                `children: ${{node.children.length}}\n` +
                `parents: ${{parents.length}}\n` +
                `parent_symbols: ${{parentSymbols}}\n` +
                `child_symbols: ${{childSymbols}}`;
        }}

        function centerOnNode(node) {{
            if (!node) return;
            if (!graphContainer) return;
            const containerRect = graphContainer.getBoundingClientRect();
            const targetX = Math.max(node.x - containerRect.width / 2, 0);
            const targetY = Math.max(node.y - containerRect.height / 2, 0);
            graphContainer.scrollTo({{ left: targetX, top: targetY, behavior: "smooth" }});
        }}

        function selectNode(node) {{
            if (!node) return;
            selectedNodeId = node.id;
            renderDetails(node);
            highlightCodeForNode(node);
            updateNodeList();
            updateGraphStyles();
        }}

        function computeLayout() {{
            const depthMap = new Map();
            nodes.forEach(node => {{
                const depth = Number.isFinite(node.depth) ? node.depth : 0;
                if (!depthMap.has(depth)) {{
                    depthMap.set(depth, []);
                }}
                depthMap.get(depth).push(node);
            }});

            const orderByDepth = new Map();
            const queue = [...graphData.roots];
            const queued = new Set(queue);
            while (queue.length > 0) {{
                const nodeId = queue.shift();
                const node = nodeById.get(nodeId);
                if (!node) continue;
                const depth = node.depth || 0;
                if (!orderByDepth.has(depth)) {{
                    orderByDepth.set(depth, []);
                }}
                if (!orderByDepth.get(depth).includes(node)) {{
                    orderByDepth.get(depth).push(node);
                }}
                node.children.forEach(childId => {{
                    if (!queued.has(childId)) {{
                        queue.push(childId);
                        queued.add(childId);
                    }}
                }});
            }}

            const depths = Array.from(depthMap.keys()).sort((a, b) => a - b);
            const columnGap = 220;
            const rowGap = 60;
            const marginX = 80;
            const marginY = 60;
            let maxNodes = 0;

            depths.forEach(depth => {{
                const level = [];
                const ordered = orderByDepth.get(depth) || [];
                ordered.forEach(node => level.push(node));

                const fallback = (depthMap.get(depth) || []).filter(node => !level.includes(node));
                fallback.sort((a, b) => {{
                    const symA = (a.symbol || "").toLowerCase();
                    const symB = (b.symbol || "").toLowerCase();
                    if (symA < symB) return -1;
                    if (symA > symB) return 1;
                    return a.id - b.id;
                }});
                fallback.forEach(node => level.push(node));

                maxNodes = Math.max(maxNodes, level.length);
                level.forEach((node, index) => {{
                    node.x = marginX + depth * columnGap;
                    node.y = marginY + index * rowGap;
                }});
            }});

            if (depths.length === 0) {{
                graphWidth = graphPanel ? graphPanel.clientWidth : window.innerWidth;
                graphHeight = graphPanel ? graphPanel.clientHeight : window.innerHeight;
                return;
            }}

            const maxDepth = Math.max(...depths);
            graphWidth = marginX * 2 + (maxDepth + 1) * columnGap;
            graphHeight = marginY * 2 + Math.max(1, maxNodes) * rowGap;

            if (graphPanel) {{
                graphWidth = Math.max(graphWidth, graphPanel.clientWidth);
                graphHeight = Math.max(graphHeight, graphPanel.clientHeight);
            }}
        }}

        function renderGraph() {{
            if (!svg) {{
                svg = d3.select("#graph-container")
                    .append("svg")
                    .attr("width", graphWidth)
                    .attr("height", graphHeight);
                g = svg.append("g");
            }} else {{
                svg.attr("width", graphWidth).attr("height", graphHeight);
            }}

            linkSelection = g.selectAll(".link")
                .data(links, d => d.source.id + "-" + d.target.id)
                .enter()
                .append("line")
                .attr("class", d => "link " + d.source.type.toLowerCase() + "-link");

            nodeSelection = g.selectAll(".node")
                .data(nodes, d => d.id)
                .enter()
                .append("g")
                .attr("class", d => "node " + d.type.toLowerCase())
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);

            nodeSelection.append("circle")
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

            nodeSelection.append("text")
                .attr("class", "node-label")
                .attr("text-anchor", "middle")
                .attr("dy", d => d.type === 'SCOPE' ? 5 : 4)
                .text(d => {{
                    const symbol = d.symbol || "";
                    if (symbol.length > 15) return symbol.substring(0, 12) + "...";
                    return symbol;
                }});

            nodeSelection.on("click", function(event, d) {{
                event.stopPropagation();
                selectNode(d);
            }});

            nodeSelection.append("title")
                .text(d => {{
                    let tooltip = d.symbol + "\\nType: " + d.type;
                    if (d.ctx) tooltip += "\\nContext: " + d.ctx;
                    tooltip += "\\nChildren: " + d.children.length;
                    return tooltip;
                }});

            updateGraphStyles();
            updatePositions();
        }}

        function updatePositions() {{
            if (!nodeSelection || !linkSelection) return;
            linkSelection
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            nodeSelection
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }}

        function updateGraphStyles() {{
            if (!nodeSelection || !linkSelection) return;
            const searchActive = matchIds.size > 0;

            nodeSelection
                .classed("selected", d => d.id === selectedNodeId)
                .classed("match", d => matchIds.has(d.id))
                .classed("dim", d => searchActive && !matchIds.has(d.id))
                .classed("hidden", d => !nodeMatchesFilter(d));

            linkSelection
                .classed("highlight", d => {{
                    return selectedNodeId !== null &&
                        (d.source.id === selectedNodeId || d.target.id === selectedNodeId);
                }})
                .classed("dim", d => {{
                    if (!searchActive) return false;
                    return !matchIds.has(d.source.id) && !matchIds.has(d.target.id);
                }})
                .classed("hidden", d => {{
                    return !nodeMatchesFilter(d.source) || !nodeMatchesFilter(d.target);
                }});
        }}

        function wireControls() {{
            const searchInput = document.getElementById("search-input");
            if (searchInput) {{
                searchInput.addEventListener("input", event => {{
                    applySearch(event.target.value);
                }});
            }}

            const scopeFilter = document.getElementById("filter-scope");
            const pushFilter = document.getElementById("filter-push");
            const popFilter = document.getElementById("filter-pop");
            const otherFilter = document.getElementById("filter-other");
            function syncFilters() {{
                if (scopeFilter) filters.SCOPE = scopeFilter.checked;
                if (pushFilter) filters.PUSH = pushFilter.checked;
                if (popFilter) filters.POP = popFilter.checked;
                if (otherFilter) filters.OTHER = otherFilter.checked;
                updateNodeList();
                updateGraphStyles();
            }}
            [scopeFilter, pushFilter, popFilter, otherFilter].forEach(control => {{
                if (control) {{
                    control.addEventListener("change", syncFilters);
                }}
            }});

            const centerBtn = document.getElementById("center-node-btn");
            if (centerBtn) {{
                centerBtn.addEventListener("click", () => {{
                    if (selectedNodeId === null) return;
                    const node = nodeById.get(selectedNodeId);
                    centerOnNode(node);
                }});
            }}
        }}
        
        // Initialize and render
        initializeGraph();
        buildCodeView();
        computeLayout();
        renderGraph();
        wireControls();
        updateNodeList();
        updateGraphStyles();
    </script>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    abs_path = os.path.abspath(output_file)
    print(f"Interactive graph visualization saved to {abs_path}")
    print(f"Statistics: {stats['total_nodes']} nodes ({stats['scope_nodes']} SCOPE, {stats['push_nodes']} PUSH, {stats['pop_nodes']} POP)")
    print("Note: Graph is rendered as a static full view. Use the inspector to search and filter.")
    return abs_path
