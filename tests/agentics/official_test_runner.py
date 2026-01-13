
import sys
import os
import re
import glob
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode

@dataclass
class Assertion:
    line_idx: int  # 0-indexed line number of the source code
    col_start: int # 0-indexed column
    col_end: int
    expected_def_lines: List[int] # 1-indexed line numbers as in the test file

class TestRunner:
    def __init__(self):
        self.builder = StackGraphBuilder("python")
        self.resolver = ReferenceResolver()
        self.failures = []

    def run_tests_in_directory(self, dir_path: str):
        print(f"Scanning {dir_path} for python test files...")
        files = glob.glob(os.path.join(dir_path, "**/*.py"), recursive=True)
        # Filter out __init__.py and this runner itself if it happens to be there
        files = [f for f in files if "runner.py" not in f and "dynamic_test.py" not in f and "__init__" not in f]
        
        print(f"Found {len(files)} test files.")
        
        for file_path in files:
            self.run_single_test_file(file_path)

        self.report()

    def run_single_test_file(self, file_path: str):
        # Read content
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            return

        # Parse assertions
        assertions = self.parse_assertions(lines)
        if not assertions:
            return

        print(f"Running {os.path.basename(file_path)} ({len(assertions)} assertions)...")
        
        # Build graph
        code = "".join(lines)
        try:
            roots = self.builder.build_from_code(code)
        except Exception as e:
            self.log_failure(file_path, code, f"Graph Build Failed: {e}")
            return

        # Validate assertions
        for assertion in assertions:
            self.verify_assertion(file_path, code, lines, roots, assertion)

    def parse_assertions(self, lines: List[str]) -> List[Assertion]:
        assertions = []
        last_code_line_idx = None
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith('#'):
                if '^' not in line:
                    continue

                # Check for "defined: <n[, n...]>" patterns
                match = re.search(r'defined:\s*([0-9,\s]+)', line)
                if not match:
                    continue

                expected_lines = [int(n) for n in re.findall(r'\d+', match.group(1))]
                if not expected_lines:
                    continue

                caret_start = line.find('^')
                caret_end = line.rfind('^') + 1

                if caret_start == -1 or last_code_line_idx is None:
                    continue

                assertions.append(Assertion(
                    line_idx=last_code_line_idx,
                    col_start=caret_start,
                    col_end=caret_end,
                    expected_def_lines=expected_lines
                ))
                continue

            if stripped:
                last_code_line_idx = i

        return assertions

    def verify_assertion(self, file_path: str, code: str, lines: List[str], roots: List[GNode], assertion: Assertion):
        # 1. Find the reference node at the location
        # Convert line_idx (0-indexed) to 1-indexed for the resolver helper provided it works that way
        # Actually my resolver helper takes file_content and line (1-indexed)
        
        ref_node = self.resolver.find_reference_by_position(
            roots, 
            assertion.line_idx + 1, 
            assertion.col_start + 1, # Column 
            code
        )

        if not ref_node:
            self.log_failure(file_path, code, 
                f"No Reference Node found at line {assertion.line_idx+1}, cols {assertion.col_start}-{assertion.col_end}")
            return
        
        # 2. Resolve
        results = self.resolver.resolve(ref_node, roots)
        
        if not results:
            self.log_failure(file_path, code,
                 f"Resolution failed for {ref_node.symbol} at line {assertion.line_idx+1}. Expected line {assertion.expected_def_lines[0]}")
            return
            
        # 3. Check definition line
        # We take the first result (highest confidence / min scope exits)
        def_node = results[0].definition
        
        # Map byte offset to line number
        def_line = self.get_line_number(code, def_node.start_byte)
        
        if def_line not in assertion.expected_def_lines:
             self.log_failure(file_path, code,
                 f"Mismatch for {ref_node.symbol} at line {assertion.line_idx+1}. "
                 f"Resolved to line {def_line}, Expected {assertion.expected_def_lines}. "
                 f"(Def Node: {def_node})")

    def get_line_number(self, code: str, byte_offset: int) -> int:
        # 1-indexed
        return code.count('\n', 0, byte_offset) + 1

    def log_failure(self, file_path: str, code: str, message: str):
        print(f"  [FAIL] {message}")
        self.failures.append({
            "file": file_path,
            "message": message,
            "code": code
        })

    def report(self):
        log_path = os.path.join(os.path.dirname(__file__), 'discrepancies.log')
        with open(log_path, 'w') as f:
            if not self.failures:
                f.write("No discrepancies found!\n")
                print("\nSUCCESS: All tests passed.")
            else:
                f.write(f"Found {len(self.failures)} discrepancies:\n\n")
                for fail in self.failures:
                    f.write("-" * 40 + "\n")
                    f.write(f"File: {fail['file']}\n")
                    f.write(f"Error: {fail['message']}\n")
                    f.write("Code snippet:\n")
                    f.write(fail['code'])
                    f.write("\n")
                print(f"\nFAILURE: Found {len(self.failures)} discrepancies. See {log_path} for details.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python official_test_runner.py <directory_with_tests>")
        sys.exit(1)
        
    runner = TestRunner()
    runner.run_tests_in_directory(sys.argv[1])
