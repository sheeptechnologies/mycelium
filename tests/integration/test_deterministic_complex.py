import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from tests.utils import run_test_case

class TestDeterministicComplex:
    def test_shadowing(self):
        """
        Verify that a local variable correctly shadows a global one.
        """
        code = """
x = 1
def foo():
    x = 2
    return x
    #      ^ defined: 4
"""
        run_test_case(code)

    def test_inheritance(self):
        """
        Verify method/attribute resolution through inheritance.
        """
        code = """
class A:
    base_attr = 1

class B(A):
    pass

val = B.base_attr
#       ^ defined: 3
"""
        run_test_case(code)

    def test_closures(self):
        """
        Verify resolution of variables in outer function scopes.
        """
        code = """
def outer():
    x = 1
    def inner():
        return x
        #      ^ defined: 3
    return inner
"""
        run_test_case(code)
