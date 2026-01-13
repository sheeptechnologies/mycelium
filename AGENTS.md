# AGENTS.md - Context & Handover Protocol

**READ THIS FIRST.**
This file is designed to help AI Agents (and humans) quickly understand the state, purpose, and conventions of the **Mycelium** project.

---

## 🧠 Project Identity
*   **Name**: Mycelium
*   **Purpose**: A library to build **stack graphs** from source code using Tree-sitter.
*   **Goal**: Replace Sourcegraph's SCIP pipeline inside **Crader** (Sheep Technologies' code indexer) with this custom, lighter, and more controllable approach.
*   **Status**: **Prototype**. APIs are evolving. Expect breaking changes.

## 🏗 System Architecture
*   **`src/captures.py`**: The "eyes". Handles Tree-sitter query compilation and dispatching.
*   **`src/graph.py`**: The "brain". Manages the graph construction and stack orchestration.
*   **`src/languages/`**: The "knowledge". Language-specific queries and handlers reside here. **Edit this to add new languages.**
*   **`src/visualizer.py`**: The "output". Renders the graph to HTML/Graphviz for debugging.
*   **`cli.py`**: The main interface for running and testing the tool manually.

## ⚠️ Operational Rules (CRITICAL)
1.  **NO AUTOMATED TESTS**:
    *   There is currently **no comprehensive automated test suite**.
    *   **Validation Protocol**: You **MUST** run `python cli.py <file> -o graph.html` (or `main.py`) and visually inspect the output in `graph.html` after making changes.
    *   Do not assume your code works just because it compiles.
2.  **Code Style**:
    *   **Clarity > Cleverness**. Use explicit names.
    *   **Modularity**: Keep parsing logic (`captures.py`) generic; put language specifics in `src/languages/`.
3.  **Documentation**:
    *   If you change an API, update the docstrings and `docs/` (MkDocs).

## 🔄 Agent Handover Context
*Use this section to leave notes for the next agent. Update this as you finish your session.*

### Current Focus
*   stabilizing the `python` language support.
*   Ensuring `StackGraphBuilder` correctly handles basic scopes and imports.
*   Visualizing the output to debug stack graph construction.

### Known Issues / Todo
*   [ ] **Testing**: We desperately need a test harness, even if it's just regression testing on `graph.html` output.
*   [ ] **Languages**: Only Python is currently being actively prototyped.
*   [ ] **Integration**: The API needs to be stabilized for `Crader` consumption.

---
*Last Updated: 2026-01-13*
