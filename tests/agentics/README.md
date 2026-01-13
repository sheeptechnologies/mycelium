
# Agentic Testing Framework

This folder exists to facilitate **Agentic Verification** of the Mycelium stack graph generator.

## Concept

Instead of rigid assertions, we generate a "raw" text representation of the stack graph and let an AI agent (like you!) verify its correctness against the original inputs and the formal definition of Stack Graphs.

## How to Run

1.  **Environment**: Ensure you are using the project's virtual environment (e.g., `env/bin/python`).
2.  **Generate Output**:

    ```
    

2.  **Run with Dynamic Generation**:
    
    To generate a random program and test it:
    ```bash
    env/bin/python tests/agentics/dynamic_test.py
    ```
    
    To run all generator templates:
    ```bash
    env/bin/python tests/agentics/dynamic_test.py all
    ```

3.  **Run Official Test Suite**:

    To verify Mycelium against the **official stack-graphs test suite** (located in `../../stack-graphs-main`), run:
    
    ```bash
    env/bin/python tests/agentics/official_test_runner.py ../../stack-graphs-main/languages/tree-sitter-stack-graphs-python/test
    ```
    
    This will:
    1.  Parse the official `.py` test files (identifying assertions like `# ^ defined: 1`).
    2.  Run Mycelium to build the graph and resolve references.
    3.  Compare the resolution results.
    4.  Log any discrepancies to `tests/agentics/discrepancies.log`.

4.  **The Agent's Job**:
    *   **Read** the "SOURCE CODE" and "STACK GRAPH" sections.
    *   **Compare** the graph structure described in the output with the generated source code.
    *   **Reference**: 
        *   **Paper**: [Stack Graphs (arXiv:2211.01224)](https://arxiv.org/pdf/2211.01224)
        *   **Implementation**: The `../../stack-graphs-main` directory contains the official Rust implementation and test data.
    *   **Logic Check**:
        *   Are definitions (POP nodes) correctly identified?
        *   Are references (PUSH nodes) properly scoped?
        *   Is the nesting hierarchy correct as per the stack graph formalism?

## Protocol

If the output is incorrect, the agent should:
1.  Identify the missing or incorrect nodes/edges.
2.  Propose fixes to `src/languages/python/` queries or handlers.
