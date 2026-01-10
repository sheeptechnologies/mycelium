"""
Base classes and utilities for language-agnostic integration tests.

This module provides abstract base classes that can be inherited by
language-specific test suites to ensure consistency and reusability.
"""

from .base_resolution_tests import BaseResolutionTestSuite
from .base_graph_tests import BaseGraphTestSuite

__all__ = [
    'BaseResolutionTestSuite',
    'BaseGraphTestSuite',
]
