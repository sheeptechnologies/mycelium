
import pytest
from tests.utils import run_test_case

class TestDeterministic:
    def test_basic_assignment(self):
        code = """
x = 1
y = x
#   ^ defined: 2
z = y
#   ^ defined: 3
"""
        run_test_case(code)

    def test_function_parameter(self):
        code = """
def foo(x):
    return x
#          ^ defined: 2
"""
        run_test_case(code)

    def test_cycle_recursion_fix(self):
        """
        Verify that our recursion fix still allows resolving cycles correctly
        (or at least doesn't crash).
        """
        code = """
class A:
    def method(self):
        self.method()
#            ^ defined: 3
"""
        run_test_case(code)

    def test_imports_mock(self):
        # Imports are harder because they span files. 
        # For this single-file runner, we can only test local resolution strictly.
        # But we can simulate "imported" behavior if we had a multi-file runner.
        # For now, let's test a local "import-like" structure (classes)
        code = """
class B:
    x = 1

val = B.x
#     ^ defined: 2
#       ^ defined: 3
"""
        run_test_case(code)
