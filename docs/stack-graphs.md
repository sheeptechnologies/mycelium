# Stack Graphs Concepts

Stack graphs are a data structure for representing lexical scoping and name resolution at scale. Mycelium follows the principles described in GitHub’s *Stack Graphs* paper: https://arxiv.org/abs/2211.01224.

---

## Core objective

Represent the semantics of a codebase by modeling:

* **Definitions** (symbol introductions).
* **References** (symbol usages).
* **Scope boundaries** and visibility rules.
* **Resolution paths** from references to definitions.

---

## Key node types

* **SCOPE**: represents a lexical context (file, class, function, or block).
* **PUSH**: introduces a symbol onto a resolution stack.
* **POP**: resolves a symbol by matching against the stack.

In Mycelium, these are encoded as `GNode` instances with `type` and `ctx` fields.

---

## Practical implications

* Tree-sitter queries define which AST nodes participate in symbol resolution.
* Handlers interpret syntax nodes and emit `GNode` structures.
* The graph builder preserves ordering and hierarchy using byte ranges.
* Accurate capture ordering is critical for deterministic name resolution.
