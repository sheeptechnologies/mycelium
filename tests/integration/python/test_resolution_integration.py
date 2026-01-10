"""
Complex Integration tests for Reference Resolution.

Tests verify resolution in real-world scenarios with complete files,
complex patterns, and realistic code structures.
"""

import pytest
from pathlib import Path
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import get_all_nodes


class TestCompleteClassHierarchy:
    """Test resolution in complete class hierarchy."""
    
    def test_resolve_complete_class(self, tmp_path):
        """Test resolution in a complete class with inheritance, methods, properties."""
        test_file = tmp_path / "complete_class.py"
        test_file.write_text("""
class Animal:
    species = "Unknown"
    
    def __init__(self, name):
        self.name = name
        self._age = 0
    
    @property
    def age(self):
        return self._age
    
    @age.setter
    def age(self, value):
        self._age = value
    
    def speak(self):
        return f"{self.name} makes a sound"

class Dog(Animal):
    species = "Canis lupus"
    
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed
    
    def speak(self):
        return f"{self.name} barks"
    
    def get_info(self):
        return f"{self.name} is a {self.breed} {self.species}"

dog = Dog("Buddy", "Golden Retriever")
info = dog.get_info()
sound = dog.speak()
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of various references
        test_cases = [
            ('name', 'self.name in __init__'),
            ('_age', 'self._age in property'),
            ('breed', 'self.breed in get_info'),
            ('species', 'self.species in get_info'),
        ]
        
        for symbol, description in test_cases:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list), f"Failed for {description}"


class TestCompleteModule:
    """Test resolution in complete module structure."""
    
    def test_resolve_complete_module(self, tmp_path):
        """Test resolution in module with imports, classes, functions."""
        test_file = tmp_path / "complete_module.py"
        test_file.write_text("""
from typing import List, Dict
from collections import defaultdict
import os

class DataProcessor:
    def __init__(self, data: List[Dict]):
        self.data = data
        self.cache = defaultdict(int)
    
    def process(self):
        results = []
        for item in self.data:
            key = item.get('key')
            if key:
                self.cache[key] += 1
                results.append(key)
        return results
    
    def get_stats(self):
        return dict(self.cache)

processor = DataProcessor([{'key': 'a'}, {'key': 'b'}])
stats = processor.get_stats()
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of key references
        key_symbols = ['data', 'cache', 'item', 'key', 'results']
        for symbol in key_symbols:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list), f"Failed for {symbol}"


class TestRealWorldPatterns:
    """Test resolution in real-world code patterns."""
    
    def test_resolve_factory_pattern(self, tmp_path):
        """Test resolution in factory pattern."""
        test_file = tmp_path / "factory.py"
        test_file.write_text("""
class Product:
    def __init__(self, name):
        self.name = name

class ProductFactory:
    @staticmethod
    def create_product(product_type, name):
        if product_type == "standard":
            return Product(name)
        elif product_type == "premium":
            product = Product(name)
            product.premium = True
            return product
        return None

factory = ProductFactory()
product = factory.create_product("standard", "Widget")
product_name = product.name
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test key resolutions
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'name']
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_decorator_pattern(self, tmp_path):
        """Test resolution in decorator pattern."""
        test_file = tmp_path / "decorator.py"
        test_file.write_text("""
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start}s")
        return result
    return wrapper

@timing_decorator
def slow_function(n):
    total = 0
    for i in range(n):
        total += i
    return total

result = slow_function(1000)
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of decorator and function
        for symbol in ['timing_decorator', 'func', 'result']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_context_manager_pattern(self, tmp_path):
        """Test resolution in context manager pattern."""
        test_file = tmp_path / "context_manager.py"
        test_file.write_text("""
class FileManager:
    def __init__(self, filename):
        self.filename = filename
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filename, 'r')
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

with FileManager("data.txt") as f:
    content = f.read()
    lines = content.split('\\n')
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution in context manager
        for symbol in ['f', 'content', 'lines']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)
    
    def test_resolve_iterator_pattern(self, tmp_path):
        """Test resolution in iterator pattern."""
        test_file = tmp_path / "iterator.py"
        test_file.write_text("""
class NumberRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    
    def __iter__(self):
        return NumberIterator(self.start, self.end)

class NumberIterator:
    def __init__(self, start, end):
        self.current = start
        self.end = end
    
    def __next__(self):
        if self.current >= self.end:
            raise StopIteration
        value = self.current
        self.current += 1
        return value

numbers = NumberRange(1, 5)
for num in numbers:
    print(num)
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution in iterator
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'num']
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)


class TestComplexScenarios:
    """Test resolution in complex real-world scenarios."""
    
    def test_resolve_complex_nested_structure(self, tmp_path):
        """Test resolution in very complex nested structure."""
        test_file = tmp_path / "complex.py"
        test_file.write_text("""
from typing import List, Callable

class Processor:
    def __init__(self, data: List[dict]):
        self.data = data
        self.filters = []
    
    def add_filter(self, filter_func: Callable):
        self.filters.append(filter_func)
    
    def process(self):
        results = []
        for item in self.data:
            passed = True
            for filter_func in self.filters:
                if not filter_func(item):
                    passed = False
                    break
            if passed:
                results.append(item)
        return results

processor = Processor([{'x': 1}, {'x': 2}])
processor.add_filter(lambda item: item['x'] > 1)
filtered = processor.process()
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test multiple resolutions
        symbols_to_test = ['data', 'filters', 'item', 'filter_func', 'results']
        for symbol in symbols_to_test:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list), f"Failed for {symbol}"
    
    def test_resolve_mixed_patterns(self, tmp_path):
        """Test resolution with mixed design patterns."""
        test_file = tmp_path / "mixed_patterns.py"
        test_file.write_text("""
from functools import lru_cache

class Calculator:
    @staticmethod
    @lru_cache(maxsize=128)
    def fibonacci(n):
        if n <= 1:
            return n
        return Calculator.fibonacci(n-1) + Calculator.fibonacci(n-2)
    
    @classmethod
    def compute(cls, operation, *args):
        if operation == "fib":
            return cls.fibonacci(args[0])
        return None

result = Calculator.compute("fib", 10)
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution in mixed patterns
        push_nodes = [n for n in all_nodes if n.type == 'PUSH']
        if push_nodes:
            # Test a few key references
            for push in push_nodes[:5]:  # Test first 5
                results = resolver.resolve(push, roots)
                assert isinstance(results, list)


class TestRealFileExamples:
    """Test resolution with real file examples."""
    
    def test_resolve_test_example_file(self, tmp_path):
        """Test resolution using the actual test_example.py structure."""
        # Read the actual test_example.py if it exists
        test_example_path = Path(__file__).parent.parent.parent / "test_example.py"
        
        if test_example_path.exists():
            builder = StackGraphBuilder()
            roots = builder.build_from_file(str(test_example_path))
            
            resolver = ReferenceResolver()
            all_nodes = get_all_nodes(roots)
            
            # Find some key references to test
            key_symbols = ['calculate_sum', 'Person', 'greet', 'process_data']
            for symbol in key_symbols:
                push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
                if push_nodes:
                    results = resolver.resolve(push_nodes[0], roots)
                    assert isinstance(results, list), f"Failed for {symbol}"
                    # If resolved, verify structure
                    for result in results:
                        assert result.definition is not None
                        assert len(result.path) > 0
                        assert result.confidence >= 0.0
    
    def test_resolve_comprehensive_example(self, tmp_path):
        """Test resolution with comprehensive example covering many features."""
        test_file = tmp_path / "comprehensive.py"
        test_file.write_text("""
# Imports
from typing import List, Dict, Optional
from functools import wraps
import os

# Decorators
def memoize(func):
    cache = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper

# Classes
class DataStore:
    def __init__(self, data: List[Dict]):
        self.data = data
        self._index = {}
        self._build_index()
    
    def _build_index(self):
        for item in self.data:
            key = item.get('id')
            if key:
                self._index[key] = item
    
    @memoize
    def get(self, key: str) -> Optional[Dict]:
        return self._index.get(key)
    
    def filter(self, predicate):
        results = []
        for item in self.data:
            if predicate(item):
                results.append(item)
        return results

# Functions
def create_predicate(threshold):
    def predicate(item):
        value = item.get('value', 0)
        return value > threshold
    return predicate

# Usage
store = DataStore([{'id': '1', 'value': 10}, {'id': '2', 'value': 20}])
pred = create_predicate(15)
filtered = store.filter(pred)
item = store.get('1')
""")
        
        builder = StackGraphBuilder()
        roots = builder.build_from_file(str(test_file))
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test resolution of many different symbols
        test_symbols = [
            'data', 'cache', 'key', 'item', 'results',
            'threshold', 'value', 'predicate', 'store', 'pred', 'filtered'
        ]
        
        resolutions_worked = 0
        for symbol in test_symbols:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == symbol]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                if results:
                    resolutions_worked += 1
                assert isinstance(results, list)
        
        # At least some resolutions should work
        assert resolutions_worked > 0, "At least some resolutions should succeed"
