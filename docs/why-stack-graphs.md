# Why Stack Graphs (and why not SCIP)

This page explains why stack graphs are a strong fit for Mycelium and why they are preferred over SCIP for Crader’s indexing pipeline.

---

## Performance foundations

Stack graphs were designed to support **fast, incremental name resolution** across large codebases. The model enables:

* **Partial paths**: resolution can be computed by composing smaller path segments, avoiding full-graph traversal for every query.
* **Incremental updates**: when a file changes, only the affected subgraph needs to be recomputed, not the entire index.
* **Composable resolution**: stack effects are local and composable, enabling efficient cache reuse.
* **Deterministic ordering**: byte-range ordering keeps graph construction stable and avoids expensive global re-sorting.

These properties reduce recomputation and allow the index to scale with fewer CPU and memory spikes than whole-project re-indexing.

---

## Why it’s faster than SCIP (in this context)

SCIP is a broad, language-server oriented indexing format. It excels as a universal interchange, but in Crader’s pipeline it introduces overhead that stack graphs can avoid:

* **Heavier schema & payload**: SCIP includes rich metadata and cross-tool compatibility that is not always needed for internal indexing.
* **Full re-indexing pressure**: SCIP workflows often favor rebuilding indexes or re-exporting large artifacts after changes.
* **Less control over resolution semantics**: Mycelium requires tight control over scoping and resolution rules, which stack graphs allow through custom handlers.

By using stack graphs directly, Mycelium focuses on **minimal semantic information** required for resolution and indexing, which reduces I/O and computational overhead.

---

## Practical implications for Crader

* **Faster incremental indexing** of large monorepos.
* **Lower storage footprint** for semantic data.
* **Greater control** over language-specific name resolution.
* **Better alignment** with custom analysis requirements.

---

## Summary

Stack graphs provide a purpose-built model for scalable, incremental name resolution. For Crader’s use case, they deliver better performance characteristics and more controllable semantics than a general-purpose interchange format like SCIP.
