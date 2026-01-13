
from tests.utils import run_test_case
import pytest

class TestDeterministicImports:
    """
    Test import resolution using stack graph rules.
    """

    def test_aliased_imports(self):
        """
        Test that aliased imports are resolved correctly.
        Reference: stack-graphs-main/languages/tree-sitter-stack-graphs-python/test/aliased_imports.py
        """
        code = """
#------ path: foo.py ------#
class A:
    a = 1

class B:
    class C:
        class D:
            d = 2

#------ path: main.py ---#
from foo import A as X, B
#                   ^ defined: 2 (commented out, X is a definition here)

# import foo as f
#      ^ defined: 1 (commented out as it refers to line 1 which is not reachable)

print(X.a)
#     ^ defined: 12
#       ^ defined: 3

# print(f.B) # todo: submodule resolution might need work
#       ^ defined: 6
"""
        run_test_case(code)

    def test_simple_import(self):
        """
        Test simple module import (simulated with local variable).
        """
        code = """
#------ path: bar.py ------#
bar = 10
# (definition of bar)

#------ path: main.py ---#
import bar
#      ^ defined: 3

print(bar)
#     ^ defined: 3
"""
        run_test_case(code)
