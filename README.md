# Mycelium

Mycelium is an experimental library that builds **stack graphs** from source code using Tree-sitter. It is inspired by GitHub’s implementation described in the *Stack Graphs* paper (https://arxiv.org/abs/2211.01224). The project is intended to replace Sourcegraph’s SCIP pipeline inside **Crader** (formerly *sheep-codebase-indexer*) with a lighter, fully controllable semantic indexing approach.

> **Project status:** Prototype. APIs and data structures are evolving and may change without notice.

---

## Why Mycelium

* **Lightweight semantic indexing** with stack graphs generated locally.
* **Full control of language semantics** through query + handler modules.
* **Direct integration path** for Crader and other Sheep Technologies tooling.
* **Debuggable output** via HTML/Graphviz visualization.

## Key capabilities

* **Tree-sitter based parsing** for robust AST extraction.
* **Capture-driven pipeline** to map syntax nodes to semantic graph nodes.
* **Modular graph builder** with a simple, extensible stack model.
* **Visualization tooling** for inspection and debugging.

---

## Project layout

```
mycelium/
├── src/
│   ├── captures.py        # Tree-sitter query compilation and dispatch
│   ├── graph.py           # Graph builder and stack orchestration
│   ├── models.py          # Core data model (GNode)
│   ├── visualizer.py      # HTML/Graphviz renderer
│   └── languages/         # Per-language queries + handlers
├── docs/                  # MkDocs documentation
├── mkdocs.yml             # Documentation configuration
└── README.md
```

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Note: documentation tooling (MkDocs + Material) is included in `requirements.txt`.

---

## Quickstart

```python
from tree_sitter import Parser
from src.captures import CapturesManager
from src.graph import GraphBuilder
from src.visualizer import visualize_graph

code = """
full_name = lambda first, last: f'Full name: {first.title()} {last.title()}'
full_name('guido', 'van rossum')
"""

manager = CapturesManager("python")
parser = Parser(manager.LANGUAGE)
root = parser.parse(code.encode("utf8")).root_node

captures = manager.execute(root)
builder = GraphBuilder()
roots = builder.build(captures, manager.get_handlers())

visualize_graph(roots)
```

Open `graph.html` in a browser to inspect the graph.

---

## Why Stack Graphs (vs SCIP)

Stack graphs offer a faster, incremental resolution model compared to SCIP. They support partial paths, file-level incremental updates, and composable resolution, which reduces recomputation and data volume for Crader. See [Why Stack Graphs](docs/why-stack-graphs.md) for details.

---

## Documentation

The documentation is maintained in `docs/` and built with MkDocs:

```bash
mkdocs serve
```

Build the static site:

```bash
mkdocs build
```

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, standards, and review expectations.

---

## Roadmap (high-level)

* Multi-language coverage with stable query/handler APIs.
* Public API stabilization for Crader integration.
* Graph persistence and serialization formats.
* Automated test suite for correctness and performance.

---

## License

TBD.
