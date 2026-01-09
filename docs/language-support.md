# Language Support

Mycelium relies on Tree-sitter and a query/handler system that maps AST nodes into stack-graph nodes.

---

## Supported languages

| Language | Status | Notes |
|---|---|---|
| Python | ✅ Prototype | Queries in `src/languages/python/queries.py` |

---

## Adding a new language

1. Add the Tree-sitter grammar package (e.g., `tree-sitter-go`).
2. Create `src/languages/<language>/`.
3. Implement `queries.py` with captures and handlers.
4. Extend `CapturesManager._load_language` to load the new `Language`.
5. Document the new language in this page and add usage notes.

---

## Query design guidelines

* Use **stable and descriptive capture names**.
* Keep definitions and references in separate queries when possible.
* Verify byte ranges to ensure correct ordering in the graph builder.
* Prefer deterministic output over aggressive optimizations.
