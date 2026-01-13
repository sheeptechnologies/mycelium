
import re
import textwrap
from typing import List, Dict, Tuple, Set
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode

def get_all_nodes(roots: List[GNode]) -> List[GNode]:
    """Get all nodes in the graph."""
    nodes = []
    visited = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if id(node) in visited:
            continue
        visited.add(id(node))
        nodes.append(node)
        stack.extend(node.children)
    return nodes

def parse_assertions(code: str) -> List[Dict]:
    """
    Parse assertion comments from code.
    
    Expected format:
    some_code()
    # ^ defined: 1, 2
    
    Returns a list of assertions:
    [
        {
            'line': 0,          # 0-indexed line of the reference
            'column': 2,        # 0-indexed column of the reference (where ^ points)
            'expected_lines': {1, 2}  # 1-indexed expected definition lines
        },
        ...
    ]
    """
    lines = code.split('\n')
    assertions = []
    
    # Regex to capture the caret and the defined line numbers
    # Group 1: Leading whitespace and caret
    # Group 2: The list of line numbers
    # Example: "    ^ defined: 1, 2"
    # We need to find the position of '^' relative to the start of the line
    
    assertion_pattern = re.compile(r'^(\s*\^)\s*defined:\s*([0-9,\s]+)$')
    
    for i, line in enumerate(lines):
        match = assertion_pattern.match(line)
        if not match:
            # Check if it's a comment with assertion inside
            # e.g. "#     ^ defined: 1"
            comment_match = re.match(r'^\s*#\s*(\^.*)$', line)
            if comment_match:
                # Process the inner part as if it was the assertion line
                content = comment_match.group(1)
                # We need to adjust column because of the '#' and whitespace
                # But wait, typically the caret aligns visually with the code above.
                # If the code is:
                # x = 1
                # # ^ defined: 1
                # The ^ is at index 2 of the comment line content (after # and space).
                # But it visually aligns with 'x' at index 0?
                # Usually in these tests, the caret position in the string matches the column in the previous line.
                # Let's assume the string index of '^' in the original line is the column.
                
                caret_index = line.find('^')
                if caret_index == -1: continue
                
                # Check if it follows "defined:"
                if "defined:" in line:
                    try:
                        defined_part = line.split("defined:")[1]
                        line_nums = {int(n.strip()) for n in defined_part.split(',') if n.strip()}
                        
                        target_line_idx = i - 1
                        # Skip previous assertion lines (comments starting with # and containing ^ defined:)
                        while target_line_idx >= 0:
                            prev_line = lines[target_line_idx]
                            # Simple heuristic: if it looks like an assertion line, skip it
                            if re.match(r'^\s*#\s*\^.*defined:', prev_line):
                                target_line_idx -= 1
                            else:
                                break
                        
                        assertions.append({
                            'line': target_line_idx, 
                            'column': caret_index,
                            'expected_lines': line_nums
                        })
                    except ValueError:
                        pass
        else:
             # This path might be taken if assertions aren't commented out, but usually they are.
             pass
             
    return assertions

def run_test_case(code: str, file_path: str = "test.py"):
    """
    Run a deterministic test case.
    
    Args:
        code: Source code with assertion comments.
        file_path: Dummy file path for the graph builder.
        
    Raises:
        AssertionError: If any assertion fails.
    """
    code = textwrap.dedent(code)
    builder = StackGraphBuilder(language='python')
    roots = builder.build_from_code(code)
    resolver = ReferenceResolver(max_paths=10000)
    
    assertions = parse_assertions(code)
    
    if not assertions:
        print("Warning: No assertions found in test case.")
        
    for assertion in assertions:
        line_idx = assertion['line']
        col_idx = assertion['column']
        expected_lines = assertion['expected_lines']
        
        # line is 0-indexed in our parser, but 1-indexed for finding reference usually?
        # let's check find_reference_by_position signature.
        # It takes 1-indexed line and 1-indexed column.
        
        ref_line = line_idx + 1
        ref_col = col_idx + 1 
        
        # Find reference
        ref_node = resolver.find_reference_by_position(roots, ref_line, ref_col, code)
        if ref_node is None:
            # Debug: print tree structure
            tree = builder.parser.parse(code.encode('utf-8'))
            print("\nTREE DUMP:")
            print(str(tree.root_node))

            # Debug: print all nodes
            print("\nGRAPH DUMP:")
            for n in get_all_nodes(roots):
                print(f"Node: {n.symbol} ({n.type}) [{n.start_byte}-{n.end_byte}] ctx={getattr(n, 'ctx', '')}")
                for c in n.children:
                    print(f"  -> Child: {c.symbol} ({c.type})")
            
            raise AssertionError(f"No reference found at line {ref_line}, col {ref_col}")
            
        # Resolve reference
        results = resolver.resolve(ref_node, roots)
        
        found_lines = set()
        for res in results:
            # Definition line
            # GNode doesn't have line number directly, need to map byte to line
            # We can re-calculate it or use a helper if available.
            # For now, let's map start_byte to line.
            def_node = res.definition
            def_line = code[:def_node.start_byte].count('\n') + 1
            found_lines.add(def_line)
            
        # Verify
        if found_lines != expected_lines:
            raise AssertionError(
                f"Resolution mismatch at line {ref_line}, col {ref_col} (symbol '{ref_node.symbol}').\n"
                f"Expected defined at: {sorted(expected_lines)}\n"
                f"Actual defined at:   {sorted(found_lines)}"
            )

