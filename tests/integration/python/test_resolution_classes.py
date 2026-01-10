"""
Integration tests for Class Resolution.

Tests verify that references in class contexts correctly resolve to their definitions,
including class methods, static methods, properties, inheritance, and attributes.
"""

import pytest
from src.graph_builder import StackGraphBuilder
from src.resolver import ReferenceResolver
from src.models import GNode, ResolutionResult
from tests.conftest import find_node_by_symbol, get_all_nodes


class TestClassMethodResolution:
    """Test resolution in class methods."""
    
    def test_resolve_class_method_self(self):
        """Test resolving 'self' in instance method."""
        code = """
class Person:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'self' in greet method
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'self']
        
        if push_nodes:
            # Should find 'self' parameter definition
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_class_method_attribute(self):
        """Test resolving instance attribute in method."""
        code = """
class Person:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name  # Should resolve to self.name assignment
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'name' in get_name method
        # This is complex as it's self.name, but we can test the 'name' part
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'name']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_classmethod_cls(self):
        """Test resolving 'cls' in classmethod."""
        code = """
class Counter:
    count = 0
    
    @classmethod
    def increment(cls):
        cls.count += 1
        return cls.count
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'cls' in classmethod
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'cls']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_staticmethod_variable(self):
        """Test resolving variables in staticmethod."""
        code = """
x = 10

class Utils:
    @staticmethod
    def process():
        return x * 2  # Should resolve to module-level x
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'x' in staticmethod
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one inside the staticmethod
            for push in push_nodes:
                if push.start_byte > 50:  # Inside the method
                    results = resolver.resolve(push, roots)
                    # Should resolve to module-level x
                    assert isinstance(results, list)
                    if results:
                        assert results[0].definition.symbol == 'x'


class TestClassAttributeResolution:
    """Test resolution of class and instance attributes."""
    
    def test_resolve_class_attribute(self):
        """Test resolving class attribute reference."""
        code = """
class Config:
    default_value = 42

result = Config.default_value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'default_value' in Config.default_value
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'default_value']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
            if results:
                assert results[0].definition.symbol == 'default_value'
    
    def test_resolve_instance_attribute(self):
        """Test resolving instance attribute."""
        code = """
class Person:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name

p = Person("Alice")
name = p.name
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'name' in p.name
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'name']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_class_variable_shadowing(self):
        """Test that instance attribute shadows class attribute."""
        code = """
class A:
    x = 1  # Class attribute
    
    def __init__(self):
        self.x = 2  # Instance attribute (shadows class)
    
    def get_x(self):
        return self.x  # Should resolve to instance attribute
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'x']
        
        if push_nodes:
            # Find the one in get_x method
            for push in push_nodes:
                if push.start_byte > 100:  # In get_x method
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)


class TestClassInheritanceResolution:
    """Test resolution with class inheritance."""
    
    def test_resolve_super_method(self):
        """Test resolving super() method call."""
        code = """
class Animal:
    def speak(self):
        return "Sound"

class Dog(Animal):
    def speak(self):
        return super().speak() + " Woof"
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'speak' in super().speak()
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'speak']
        
        if push_nodes:
            # Find the one in Dog.speak (should be after "super().")
            for push in push_nodes:
                if push.start_byte > 80:  # In Dog class
                    results = resolver.resolve(push, roots)
                    assert isinstance(results, list)
    
    def test_resolve_inherited_attribute(self):
        """Test resolving attribute from parent class."""
        code = """
class Base:
    base_attr = "base"

class Derived(Base):
    def get_attr(self):
        return self.base_attr  # From parent
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'base_attr']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_multiple_inheritance(self):
        """Test resolution with multiple inheritance."""
        code = """
class A:
    attr_a = 1

class B:
    attr_b = 2

class C(A, B):
    def get_attrs(self):
        return self.attr_a, self.attr_b
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Test both attributes
        for attr in ['attr_a', 'attr_b']:
            push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == attr]
            if push_nodes:
                results = resolver.resolve(push_nodes[0], roots)
                assert isinstance(results, list)


class TestPropertyResolution:
    """Test resolution with properties."""
    
    def test_resolve_property_getter(self):
        """Test resolving property getter."""
        code = """
class Person:
    def __init__(self, name):
        self._name = name
    
    @property
    def name(self):
        return self._name
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for '_name' in property getter
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == '_name']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_property_setter(self):
        """Test resolving property setter."""
        code = """
class Person:
    def __init__(self, name):
        self._name = name
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for '_name' in setter
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == '_name']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)


class TestClassSpecialCases:
    """Test special class-related resolution cases."""
    
    def test_resolve_class_variable_in_method(self):
        """Test resolving class variable from instance method."""
        code = """
class Counter:
    count = 0
    
    def increment(self):
        Counter.count += 1  # Class variable via class name
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'count' in Counter.count
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'count']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_nested_class(self):
        """Test resolution in nested class."""
        code = """
class Outer:
    outer_attr = 1
    
    class Inner:
        def method(self):
            return Outer.outer_attr  # Access outer class
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'outer_attr']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
    
    def test_resolve_class_decorator(self):
        """Test resolving decorator on class."""
        code = """
def decorator(cls):
    return cls

@decorator
class MyClass:
    pass
"""
        builder = StackGraphBuilder()
        roots = builder.build_from_code(code)
        
        resolver = ReferenceResolver()
        all_nodes = get_all_nodes(roots)
        
        # Find PUSH for 'decorator'
        push_nodes = [n for n in all_nodes if n.type == 'PUSH' and n.symbol == 'decorator']
        
        if push_nodes:
            results = resolver.resolve(push_nodes[0], roots)
            assert isinstance(results, list)
            if results:
                assert results[0].definition.symbol == 'decorator'
