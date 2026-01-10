"""
Comprehensive example Python file for testing Mycelium stack graphs.
This file demonstrates various Python features including imports, classes, 
functions, decorators, control flow, exceptions, and more.
"""

# ============================================================================
# IMPORTS - Various import styles
# ============================================================================

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
from collections import defaultdict, Counter
from functools import wraps, lru_cache
import json as json_lib

# Aliased imports
import numpy as np
import pandas as pd

# Relative imports (commented for standalone file)
# from .utils import helper_function
# from ..config import settings

# Wildcard import example (commented - not recommended)
# from math import *


# ============================================================================
# DECORATORS
# ============================================================================

def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

def deprecated(func: Callable) -> Callable:
    """Mark a function as deprecated."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Warning: {func.__name__} is deprecated")
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# CLASSES
# ============================================================================

class Person:
    """A person class with methods and properties."""
    
    def __init__(self, name: str, age: int, email: Optional[str] = None):
        self.name = name
        self.age = age
        self.email = email
        self._friends: List['Person'] = []
    
    @property
    def is_adult(self) -> bool:
        """Check if person is an adult."""
        return self.age >= 18
    
    def add_friend(self, friend: 'Person') -> None:
        """Add a friend to the person's friend list."""
        if friend not in self._friends:
            self._friends.append(friend)
    
    def get_friends(self) -> List['Person']:
        """Get list of friends."""
        return self._friends.copy()
    
    def introduce(self) -> str:
        """Introduce the person."""
        return f"I'm {self.name}, {self.age} years old."


class Employee(Person):
    """Employee class inheriting from Person."""
    
    def __init__(self, name: str, age: int, employee_id: str, salary: float):
        super().__init__(name, age)
        self.employee_id = employee_id
        self.salary = salary
        self.department: Optional[str] = None
    
    def assign_department(self, department: str) -> None:
        """Assign employee to a department."""
        self.department = department
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Employee':
        """Create Employee from dictionary."""
        return cls(
            name=data['name'],
            age=data['age'],
            employee_id=data['employee_id'],
            salary=data['salary']
        )
    
    @staticmethod
    def calculate_bonus(salary: float, performance: float) -> float:
        """Calculate bonus based on salary and performance."""
        return salary * performance * 0.1


# ============================================================================
# FUNCTIONS
# ============================================================================

@timing_decorator
def greet(name: str, title: Optional[str] = None) -> str:
    """Greet a person by name with optional title."""
    if title:
        return f"Hello, {title} {name}!"
    return f"Hello, {name}!"


@deprecated
def old_function(x: int) -> int:
    """An old deprecated function."""
    return x * 2


@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Calculate Fibonacci number with memoization."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def process_data(data: List[Dict], filter_func: Optional[Callable] = None) -> List[Dict]:
    """Process a list of dictionaries with optional filtering."""
    if filter_func:
        data = [item for item in data if filter_func(item)]
    
    # Process each item
    result = []
    for item in data:
        processed = {
            'id': item.get('id'),
            'value': item.get('value', 0) * 2,
            'timestamp': Path(__file__).stat().st_mtime
        }
        result.append(processed)
    
    return result


def divide_numbers(a: float, b: float) -> float:
    """Divide two numbers with error handling."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


# ============================================================================
# CONTROL FLOW
# ============================================================================

def categorize_age(age: int) -> str:
    """Categorize age using if/elif/else."""
    if age < 13:
        return "Child"
    elif age < 18:
        return "Teenager"
    elif age < 65:
        return "Adult"
    else:
        return "Senior"


def process_items(items: List[str]) -> Dict[str, int]:
    """Process items using for loop and dictionary comprehension."""
    counts = defaultdict(int)
    
    for item in items:
        counts[item.lower()] += 1
    
    # Dictionary comprehension
    filtered = {k: v for k, v in counts.items() if v > 1}
    
    return filtered


def find_max(numbers: List[int]) -> Optional[int]:
    """Find maximum using while loop."""
    if not numbers:
        return None
    
    max_val = numbers[0]
    i = 1
    
    while i < len(numbers):
        if numbers[i] > max_val:
            max_val = numbers[i]
        i += 1
    
    return max_val


# ============================================================================
# EXCEPTIONS
# ============================================================================

def safe_divide(a: float, b: float) -> Optional[float]:
    """Safely divide two numbers with exception handling."""
    try:
        result = a / b
        return result
    except ZeroDivisionError as e:
        print(f"Error: {e}")
        return None
    except TypeError as e:
        print(f"Type error: {e}")
        return None
    finally:
        print("Division operation completed")


def read_config_file(filepath: str) -> Dict:
    """Read configuration file with multiple exception types."""
    try:
        with open(filepath, 'r') as f:
            config = json_lib.load(f)
        return config
    except FileNotFoundError:
        print(f"Config file not found: {filepath}")
        return {}
    except json_lib.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

def write_to_file(filename: str, content: str) -> None:
    """Write content to file using context manager."""
    with open(filename, 'w') as f:
        f.write(content)
    
    # File is automatically closed here


def process_file(filename: str) -> List[str]:
    """Process file line by line."""
    lines = []
    with open(filename, 'r') as file:
        for line in file:
            processed = line.strip().upper()
            lines.append(processed)
    return lines


# ============================================================================
# COMPREHENSIONS
# ============================================================================

def create_squares(n: int) -> List[int]:
    """Create list of squares using list comprehension."""
    return [x ** 2 for x in range(n)]


def filter_evens(numbers: List[int]) -> List[int]:
    """Filter even numbers with conditional comprehension."""
    return [x for x in numbers if x % 2 == 0]


def create_mapping(names: List[str]) -> Dict[str, int]:
    """Create name to length mapping using dict comprehension."""
    return {name: len(name) for name in names}


def create_unique_set(items: List[str]) -> set:
    """Create set using set comprehension."""
    return {item.lower() for item in items}


# ============================================================================
# LAMBDA AND FUNCTIONAL PROGRAMMING
# ============================================================================

def apply_operations(numbers: List[int]) -> List[int]:
    """Apply operations using lambda and map."""
    doubled = list(map(lambda x: x * 2, numbers))
    filtered = list(filter(lambda x: x > 10, doubled))
    return filtered


# ============================================================================
# PATTERN MATCHING (Python 3.10+)
# ============================================================================

def handle_response(response: Dict) -> str:
    """Handle response using pattern matching (Python 3.10+)."""
    # Note: This requires Python 3.10+
    # match response.get('status'):
    #     case 200:
    #         return "Success"
    #     case 404:
    #         return "Not Found"
    #     case 500:
    #         return "Server Error"
    #     case _:
    #         return "Unknown"
    
    # Fallback for older Python versions
    status = response.get('status', 0)
    if status == 200:
        return "Success"
    elif status == 404:
        return "Not Found"
    elif status == 500:
        return "Server Error"
    else:
        return "Unknown"


# ============================================================================
# ADVANCED FEATURES
# ============================================================================

def process_with_defaults(data: Dict, defaults: Optional[Dict] = None) -> Dict:
    """Process data with default values using walrus operator."""
    defaults = defaults or {}
    
    # Using walrus operator (Python 3.8+)
    if (value := data.get('key')) is not None:
        return {'processed': value * 2}
    
    return {'processed': defaults.get('key', 0)}


def unpack_example(*args, **kwargs) -> tuple:
    """Example of unpacking arguments."""
    positional = list(args)
    keyword = dict(kwargs)
    return (positional, keyword)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function demonstrating various features."""
    # Create instances
    person = Person("Alice", 30, "alice@example.com")
    employee = Employee("Bob", 35, "EMP001", 75000.0)
    
    # Use methods
    greeting = greet(person.name, "Ms.")
    print(greeting)
    
    # Add friends
    friend = Person("Charlie", 28)
    person.add_friend(friend)
    
    # Process data
    data = [
        {'id': 1, 'value': 10},
        {'id': 2, 'value': 20},
        {'id': 3, 'value': 30}
    ]
    processed = process_data(data, lambda x: x['value'] > 15)
    
    # Use comprehensions
    squares = create_squares(10)
    evens = filter_evens([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    # Exception handling
    result = safe_divide(10, 2)
    result2 = safe_divide(10, 0)
    
    # File operations
    try:
        config = read_config_file("config.json")
    except Exception as e:
        print(f"Failed to read config: {e}")
    
    # Use imports
    path = Path(__file__)
    print(f"Current file: {path.name}")
    
    # Use numpy (if available)
    try:
        arr = np.array([1, 2, 3, 4, 5])
        mean = np.mean(arr)
        print(f"Mean: {mean}")
    except ImportError:
        print("NumPy not available")
    
    print("All operations completed!")


if __name__ == "__main__":
    main()
