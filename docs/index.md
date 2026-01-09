# Mycelium

Mycelium is an experimental library for generating **stack graphs** from source code using Tree-sitter. It is inspired by GitHub’s Stack Graphs implementation described in the paper https://arxiv.org/abs/2211.01224. The library is designed to replace Sourcegraph’s SCIP pipeline in **Crader** (formerly *sheep-codebase-indexer*) with a lighter, fully controlled semantic indexer.

---

## Goals

* Provide **local semantic indexing** without external infrastructure.
* Enable **precise control of language semantics** via queries and handlers.
* Deliver **consistent integration** for Crader and other internal tooling.
* Offer **debuggable output** through visual inspection and deterministic builds.

---

## Current status

Mycelium is in **prototype** stage. APIs and models are not yet stable and may change.

---

## Documentation map

* [Getting Started](getting-started.md)
* [Architecture](architecture.md)
* [Stack Graphs Concepts](stack-graphs.md)
* [Language Support](language-support.md)
* [Development](development.md)

---

For contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).
