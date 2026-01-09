# Getting Started

This guide walks you through installing and running Mycelium locally.

---

## Requirements

* Python 3.10+ recommended.
* `pip` or `pipx`.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Minimal example

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

Open `graph.html` in a browser to inspect the result.

---

## Running the example script

A demo script is available in `main.py`:

```bash
python main.py
```

---

## Building documentation

```bash
mkdocs serve
```

Build static output:

```bash
mkdocs build
```
