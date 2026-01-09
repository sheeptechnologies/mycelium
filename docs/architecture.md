# Architecture

Mycelium implements a modular pipeline to generate stack graphs from Tree-sitter syntax trees.

---

## Pipeline overview

1. **Parsing**: Tree-sitter parses source code into a typed AST.
2. **Captures**: Tree-sitter queries select relevant AST nodes.
3. **Handlers**: language-specific handlers translate captures into semantic nodes.
4. **Graph Builder**: combines handler output into a unified graph.
5. **Visualization**: outputs HTML for inspection and debugging.

---

## Core modules

### `src/captures.py`

* Loads the requested Tree-sitter language.
* Compiles multiple query strings into a single `Query` object.
* Provides a **dispatch map** that binds capture names to handlers.

### `src/graph.py`

* Implements the `GraphBuilder` and stack-based processing.
* Orders captures by byte range to preserve hierarchy.
* Aggregates handler output into `GNode` structures.

### `src/models.py`

* Defines `GNode`, the core graph node abstraction.
* Tracks `symbol`, `type`, `ctx`, and parent/child relationships.

### `src/visualizer.py`

* Produces standalone HTML for graph visualization.
* Uses subgraph clusters to represent scope boundaries.
* Applies distinct styling for PUSH/POP nodes.

---

## Architectural principles

* **Separation of concerns**: parsing, capturing, and building are distinct.
* **Extensibility**: language support should be added without touching core modules.
* **Determinism**: the graph builder must produce stable, repeatable output.
* **Integration-first design**: output should be compatible with Crader expectations.

---

## Technical roadmap

* Multi-language coverage with validated query suites.
* Stable node schema and serialization format.
* Automated regression tests on curated corpora.
* Performance profiling and memory optimization.
