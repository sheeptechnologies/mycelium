# Contributing to Mycelium

Thank you for your interest in contributing to Mycelium. This document describes expectations, quality standards, and the collaboration workflow.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Local setup](#local-setup)
3. [Project structure](#project-structure)
4. [Development guidelines](#development-guidelines)
5. [Language queries & handlers](#language-queries--handlers)
6. [Testing & verification](#testing--verification)
7. [Documentation](#documentation)
8. [Commit conventions](#commit-conventions)
9. [Pull requests](#pull-requests)

---

## Prerequisites

* Python 3.10+ (recommended).
* `pip` or `pipx`.
* Basic knowledge of Tree-sitter and stack graph concepts.

---

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Project structure

* **`src/captures.py`**: Tree-sitter parsing, query compilation, capture dispatch.
* **`src/graph.py`**: graph construction and stack orchestration.
* **`src/models.py`**: core data model (`GNode`).
* **`src/languages/`**: language-specific queries and handlers.
* **`src/visualizer.py`**: HTML visualization for debugging.
* **`docs/`**: MkDocs documentation site.

---

## Development guidelines

* **Clarity first:** prefer explicit names, minimal side effects, and short docstrings.
* **Modularity:** keep parsing, capturing, and graph logic independent.
* **Stability:** avoid breaking changes without an explicit rationale and doc updates.
* **Compatibility:** ensure changes remain aligned with Crader integration goals.
* **Observability:** add or update logging/visualization where it improves debugging.

---

## Language queries & handlers

1. Add or update queries in `src/languages/<language>/queries.py`.
2. Ensure captures have consistent, descriptive names.
3. Provide handlers that map AST nodes to `GNode` structures.
4. Verify byte ranges and ordering for deterministic graph construction.
5. Update documentation under `docs/` when introducing new language support.

---

## Testing & verification

There is no automated test suite yet. For each change:

* Run the example in `main.py`.
* Validate the generated graph output (e.g., `graph.html`).
* Sanity-check ordering and scoping behavior in captured nodes.

---

## Documentation

Documentation is built with MkDocs.

```bash
mkdocs serve
```

Generate static output:

```bash
mkdocs build
```

---

## Commit conventions

* Use small, focused commits with descriptive messages.
* Include context and rationale in commit messages when behavior changes.

---

## Pull requests

1. Create a dedicated branch.
2. Describe what changed and why.
3. List manual checks/tests executed.
4. Update docs when APIs or behavior change.

Thank you for your contribution.
