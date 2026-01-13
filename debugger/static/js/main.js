// Global state
let currentCodebase = null;
let currentFile = null;
let currentCode = '';
let currentGraph = null;
let pathHighlights = [];

// API base URL
const API_BASE = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    
    // Allow Enter key in codebase path input
    document.getElementById('codebase-path').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadCodebase();
        }
    });
});

function setupEventListeners() {
    // Editor click handler - will be set up after code is loaded
}

// Load codebase
async function loadCodebase() {
    const pathInput = document.getElementById('codebase-path');
    const codebasePath = pathInput.value.trim();
    
    if (!codebasePath) {
        showError('Please enter a codebase path');
        return;
    }
    
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '<div class="loading"></div> Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/api/load_codebase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: codebasePath })
        });
        
        const data = await response.json();
        
        if (data.status === 'error') {
            showError(data.error || 'Failed to load codebase');
            fileList.innerHTML = '';
            return;
        }
        
        currentCodebase = codebasePath;
        displayFileList(data.files);
        
    } catch (error) {
        showError(`Error loading codebase: ${error.message}`);
        fileList.innerHTML = '';
    }
}

// Display file list
function displayFileList(files) {
    const fileList = document.getElementById('file-list');
    
    if (files.length === 0) {
        fileList.innerHTML = '<p class="placeholder">No Python files found</p>';
        return;
    }
    
    fileList.innerHTML = files.map((file, index) => `
        <div class="file-item" data-file-path="${escapeHtml(file.path)}" data-file-name="${escapeHtml(file.name)}" onclick="loadFileFromList(this)">
            <div class="file-name">${escapeHtml(file.name)}</div>
            <div class="file-path">${escapeHtml(file.relative_path)}</div>
        </div>
    `).join('');
}

// Load file from list item click
function loadFileFromList(element) {
    const filePath = element.getAttribute('data-file-path');
    const fileName = element.getAttribute('data-file-name');
    loadFile(filePath, fileName, element);
}

// Load file
async function loadFile(filePath, fileName, activeElement) {
    // Update active file in list
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('active');
    });
    if (activeElement) {
        activeElement.classList.add('active');
    }
    
    currentFile = filePath;
    document.getElementById('current-file-name').textContent = fileName;
    document.getElementById('build-graph-btn').disabled = false;
    
    // Clear previous highlights
    clearHighlights();
    
    try {
        const response = await fetch(`${API_BASE}/api/load_file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_path: filePath })
        });
        
        const data = await response.json();
        
        if (data.status === 'error') {
            showError(data.error || 'Failed to load file');
            return;
        }
        
        currentCode = data.content;
        displayCode(data.content);
        
        // Setup click handler after code is displayed
        setupCodeClickHandler();
        
    } catch (error) {
        showError(`Error loading file: ${error.message}`);
    }
}

// Display code with syntax highlighting
function displayCode(code) {
    const codeElement = document.getElementById('code-content');
    codeElement.textContent = code;
    
    // Apply Prism highlighting
    Prism.highlightElement(codeElement);
    
    // Wrap each token in a span for click detection
    wrapTokensForClick(codeElement);
}

// Wrap tokens for click detection
function wrapTokensForClick(codeElement) {
    // Prism already wraps tokens, but we need to make them clickable
    // We'll add click handlers to the parent pre element and calculate position
}

// Setup click handler for code editor
function setupCodeClickHandler() {
    const editor = document.getElementById('editor');
    
    // Remove old handler if exists
    editor.removeEventListener('click', handleCodeClick);
    
    // Add new handler
    editor.addEventListener('click', handleCodeClick);
}

// Handle click on code
async function handleCodeClick(event) {
    // Don't handle clicks on path panel items
    if (event.target.closest('.path-item')) {
        return;
    }
    
    const codeElement = document.getElementById('code-content');
    if (!codeElement.contains(event.target)) {
        return;
    }
    
    // Calculate line and column from click position
    const { line, column } = getPositionFromClick(event, codeElement);
    
    if (!line || !column) {
        return;
    }
    
    // Clear previous highlights
    clearHighlights();
    
    // Show loading
    const pathDisplay = document.getElementById('path-display');
    pathDisplay.innerHTML = '<div class="loading"></div> Resolving...';
    
    try {
        // First build graph if not already built
        if (!currentGraph) {
            await buildGraph();
        }
        
        // Resolve reference
        const response = await fetch(`${API_BASE}/api/resolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: currentFile,
                code: currentCode,
                line: line,
                column: column
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'error') {
            showError(data.error || 'Failed to resolve reference');
            return;
        }
        
        if (data.results.length === 0) {
            pathDisplay.innerHTML = '<p class="placeholder">No definition found at this position</p>';
            return;
        }
        
        // Display path
        displayPath(data.results[0], data.reference);
        
        // Highlight path in code
        highlightPath(data.results[0].path, data.reference);
        
    } catch (error) {
        showError(`Error resolving reference: ${error.message}`);
    }
}

// Get line and column from click position
function getPositionFromClick(event, codeElement) {
    const pre = codeElement.parentElement;
    const rect = pre.getBoundingClientRect();
    
    // Get click position relative to pre element
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Calculate which line
    const lineHeight = parseFloat(getComputedStyle(pre).lineHeight) || 20;
    const paddingTop = parseFloat(getComputedStyle(pre).paddingTop) || 16;
    
    const line = Math.floor((y - paddingTop) / lineHeight) + 1;
    
    // Calculate column
    // Get text up to the clicked line
    const lines = currentCode.split('\n');
    if (line < 1 || line > lines.length) {
        return { line: null, column: null };
    }
    
    // Get the line text
    const lineText = lines[line - 1];
    
    // Approximate column from x position
    // This is approximate - for exact calculation we'd need to measure character widths
    const charWidth = 8.4; // Approximate monospace character width
    const paddingLeft = parseFloat(getComputedStyle(pre).paddingLeft) || 16;
    const column = Math.floor((x - paddingLeft) / charWidth) + 1;
    
    return { 
        line: Math.max(1, line), 
        column: Math.max(1, Math.min(column, lineText.length + 1))
    };
}

// Build graph
async function buildGraph() {
    if (!currentCode) {
        showError('No code loaded');
        return;
    }
    
    const btn = document.getElementById('build-graph-btn');
    btn.disabled = true;
    btn.textContent = 'Building...';
    
    try {
        const response = await fetch(`${API_BASE}/api/build_graph`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: currentFile,
                code: currentCode
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'error') {
            showError(data.error || 'Failed to build graph');
            btn.disabled = false;
            btn.textContent = 'Build Graph';
            return;
        }
        
        currentGraph = true;
        btn.textContent = `Graph Built (${data.node_count} nodes)`;
        btn.style.backgroundColor = '#4ec9b0';
        
        // Show success message
        showSuccess(`Graph built successfully with ${data.node_count} nodes`);
        
    } catch (error) {
        showError(`Error building graph: ${error.message}`);
        btn.disabled = false;
        btn.textContent = 'Build Graph';
    }
}

// Display resolution path
function displayPath(result, reference) {
    const pathDisplay = document.getElementById('path-display');
    
    if (!result || !result.path || result.path.length === 0) {
        pathDisplay.innerHTML = '<p class="placeholder">No path found</p>';
        return;
    }
    
    const path = result.path;
    const definition = result.definition;
    const confidence = result.confidence || 0;
    
    let html = `
        <div class="path-item definition">
            <div class="path-item-header">
                <span class="path-item-symbol">${escapeHtml(definition.symbol)}</span>
                <span class="path-item-type ${definition.type}">${definition.type}</span>
            </div>
            <div class="path-item-details">
                <span>Definition</span>
                <span>Bytes: ${definition.start_byte}-${definition.end_byte}</span>
            </div>
            <div class="confidence-badge ${getConfidenceClass(confidence)}">
                Confidence: ${(confidence * 100).toFixed(1)}%
            </div>
        </div>
    `;
    
    // Add reference at the start
    if (reference) {
        html = `
            <div class="path-item reference">
                <div class="path-item-header">
                    <span class="path-item-symbol">${escapeHtml(reference.symbol)}</span>
                    <span class="path-item-type ${reference.type}">${reference.type}</span>
                </div>
                <div class="path-item-details">
                    <span>Reference (clicked)</span>
                    <span>Bytes: ${reference.start_byte}-${reference.end_byte}</span>
                </div>
            </div>
            <div style="text-align: center; padding: 8px; color: #858585;">↓</div>
        ` + html;
    }
    
    // Add intermediate nodes
    if (path.length > 2) {
        html += '<div style="text-align: center; padding: 8px; color: #858585;">Path nodes:</div>';
        for (let i = 1; i < path.length - 1; i++) {
            const node = path[i];
            html += `
                <div class="path-item" onclick="highlightNode(${node.start_byte}, ${node.end_byte})">
                    <div class="path-item-header">
                        <span class="path-item-symbol">${escapeHtml(node.symbol)}</span>
                        <span class="path-item-type ${node.type}">${node.type}</span>
                    </div>
                    <div class="path-item-details">
                        <span>Bytes: ${node.start_byte}-${node.end_byte}</span>
                    </div>
                </div>
            `;
        }
    }
    
    pathDisplay.innerHTML = html;
}

// Highlight path in code
function highlightPath(path, reference) {
    clearHighlights();
    
    const codeElement = document.getElementById('code-content');
    const code = currentCode;
    
    // Create a map of byte ranges to highlight
    const highlights = [];
    
    // Highlight reference
    if (reference) {
        highlights.push({
            start: reference.start_byte,
            end: reference.end_byte,
            class: 'path-node-reference'
        });
    }
    
    // Highlight path nodes
    path.forEach(node => {
        highlights.push({
            start: node.start_byte,
            end: node.end_byte,
            class: node.type === 'POP' ? 'path-node-definition' : 'path-node-highlight'
        });
    });
    
    // Sort by start byte
    highlights.sort((a, b) => a.start - b.start);
    
    // Apply highlights
    applyHighlights(highlights, code);
}

// Apply highlights to code
function applyHighlights(highlights, code) {
    const codeElement = document.getElementById('code-content');
    const pre = codeElement.parentElement;
    
    // Simple approach: highlight lines that contain highlighted bytes
    const lines = code.split('\n');
    let currentByte = 0;
    
    lines.forEach((line, index) => {
        const lineBytes = new TextEncoder().encode(line).length;
        const lineStartByte = currentByte;
        const lineEndByte = currentByte + lineBytes;
        
        // Check if any highlight overlaps this line
        const lineHighlights = highlights.filter(h => 
            (h.start >= lineStartByte && h.start < lineEndByte) ||
            (h.end > lineStartByte && h.end <= lineEndByte) ||
            (h.start <= lineStartByte && h.end >= lineEndByte)
        );
        
        if (lineHighlights.length > 0) {
            // Find the most specific highlight (definition > reference > other)
            let highlightClass = 'path-node-highlight';
            if (lineHighlights.some(h => h.class === 'path-node-definition')) {
                highlightClass = 'path-node-definition';
            } else if (lineHighlights.some(h => h.class === 'path-node-reference')) {
                highlightClass = 'path-node-reference';
            }
            
            // Create a wrapper for the line
            const lineWrapper = document.createElement('span');
            lineWrapper.className = highlightClass;
            lineWrapper.style.display = 'block';
            lineWrapper.style.padding = '2px 0';
            lineWrapper.style.margin = '0 -16px';
            lineWrapper.style.paddingLeft = '16px';
            lineWrapper.style.paddingRight = '16px';
            
            // We'll use a simpler approach: add class to pre and use CSS
            // For now, just mark the line
            pre.setAttribute('data-highlight-line', index + 1);
            pathHighlights.push(pre);
        }
        
        currentByte = lineEndByte + 1; // +1 for newline
    });
    
    // Apply CSS class to pre for line highlighting
    if (pathHighlights.length > 0) {
        pre.classList.add('has-highlights');
    }
}

// Helper functions
function getCharFromByte(byteOffset, text) {
    const encoder = new TextEncoder();
    let charOffset = 0;
    let byteCount = 0;
    
    for (let i = 0; i < text.length; i++) {
        const charBytes = encoder.encode(text[i]).length;
        if (byteCount + charBytes > byteOffset) {
            return charOffset;
        }
        byteCount += charBytes;
        charOffset++;
    }
    
    return charOffset;
}

function getLineFromChar(charOffset, text) {
    const lines = text.substring(0, charOffset).split('\n');
    return lines.length;
}

function clearHighlights() {
    pathHighlights.forEach(el => {
        el.classList.remove('path-node-highlight', 'path-node-definition', 'path-node-reference');
    });
    pathHighlights = [];
}

function highlightNode(startByte, endByte) {
    // Scroll to and highlight a specific node
    clearHighlights();
    // Implementation for scrolling to node
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
}

function showError(message) {
    const pathDisplay = document.getElementById('path-display');
    pathDisplay.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
}

function showSuccess(message) {
    // Show success message temporarily
    const pathDisplay = document.getElementById('path-display');
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    pathDisplay.insertBefore(successDiv, pathDisplay.firstChild);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
