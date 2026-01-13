# Mycelium Stack Graph Debugger

Web-based debugger interface for visualizing and debugging stack graph resolution (go to definition).

## Features

- **Codebase Browser**: Load and browse Python codebases
- **Code Editor**: View code with syntax highlighting
- **Interactive Resolution**: Click on any reference in the code to see its resolution path
- **Path Visualization**: View the complete resolution path in a side panel
- **Graph Building**: Build stack graphs for files and cache them for performance

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure Flask and flask-cors are installed:
```bash
pip install flask flask-cors
```

## Usage

1. Start the debugger server:
```bash
cd debugger
python app.py
```

**Note**: The debugger automatically adds the parent directory to Python path, so you can run it from the `debugger/` directory. Alternatively, you can run it from the project root:

```bash
python -m debugger.app
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. **Load a codebase**:
   - Enter the path to a directory containing Python files
   - Click "Load" to scan for Python files

4. **Open a file**:
   - Click on any file in the left sidebar to load it in the editor

5. **Build the graph** (optional but recommended):
   - Click "Build Graph" to construct the stack graph for the current file
   - This will be cached for faster resolution

6. **Resolve a reference**:
   - Click on any identifier (variable, function, class, etc.) in the code
   - The resolution path will appear in the right sidebar
   - The path nodes will be highlighted in the code

## API Endpoints

The debugger provides the following REST API endpoints:

### `POST /api/load_codebase`
Load and scan a codebase directory.

**Request:**
```json
{
  "path": "/path/to/codebase"
}
```

**Response:**
```json
{
  "files": [
    {
      "name": "file.py",
      "path": "/absolute/path/to/file.py",
      "relative_path": "file.py"
    }
  ],
  "status": "ok",
  "count": 10
}
```

### `POST /api/load_file`
Load the content of a file.

**Request:**
```json
{
  "file_path": "/path/to/file.py"
}
```

**Response:**
```json
{
  "content": "file content...",
  "status": "ok",
  "file_path": "/path/to/file.py"
}
```

### `POST /api/build_graph`
Build a stack graph for a file.

**Request:**
```json
{
  "file_path": "/path/to/file.py",
  "code": "code content..."
}
```

**Response:**
```json
{
  "status": "ok",
  "node_count": 42,
  "cached": false
}
```

### `POST /api/find_reference`
Find a reference node at a specific position.

**Request:**
```json
{
  "file_path": "/path/to/file.py",
  "code": "code content...",
  "line": 5,
  "column": 10
}
```

**Response:**
```json
{
  "reference": {
    "symbol": "x",
    "type": "PUSH",
    "start_byte": 45,
    "end_byte": 46
  },
  "status": "ok"
}
```

### `POST /api/resolve`
Resolve a reference to its definition(s).

**Request:**
```json
{
  "file_path": "/path/to/file.py",
  "code": "code content...",
  "line": 5,
  "column": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "definition": {
        "symbol": "x",
        "type": "POP",
        "start_byte": 10,
        "end_byte": 11
      },
      "path": [
        {"symbol": "x", "type": "PUSH", ...},
        ...
        {"symbol": "x", "type": "POP", ...}
      ],
      "confidence": 0.95
    }
  ],
  "status": "ok",
  "reference": {...}
}
```

## Architecture

- **Backend**: Flask server providing REST API
- **Frontend**: HTML/CSS/JavaScript with Prism.js for syntax highlighting
- **Integration**: Uses `StackGraphBuilder` and `ReferenceResolver` from the main library

## Limitations

- Currently supports Python only
- Single-file resolution (no cross-file support yet)
- Click detection is approximate (uses line/column estimation)
- Graph caching is per-session only

## Future Enhancements

- Multi-file resolution support
- Visual graph representation
- Export resolution paths
- Support for other languages
- Persistent graph caching
- Better click position detection
