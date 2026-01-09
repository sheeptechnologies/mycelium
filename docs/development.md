# Development

This page summarizes the expected development workflow and quality standards for Mycelium.

---

## Recommended workflow

1. Create a dedicated branch.
2. Implement changes with small, focused commits.
3. Update documentation and examples as needed.
4. Run manual verification steps before submitting.

---

## Quality standards

* **Readable code** with explicit naming and minimal side effects.
* **Stable public APIs** and documented behavior.
* **Minimal breaking changes** unless explicitly justified.
* **Crader alignment** for any semantic changes.

---

## Debugging & visualization

The HTML visualizer in `src/visualizer.py` is the primary debugging tool for validating graph output. Use it after modifying queries or handlers.

---

## Documentation

* `mkdocs serve` for local development.
* `mkdocs build` for static output generation.

---

## More details

See [CONTRIBUTING.md](../CONTRIBUTING.md) for a complete contribution guide.
