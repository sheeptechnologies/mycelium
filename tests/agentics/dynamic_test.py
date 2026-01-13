
import sys
import os
import random
import string
from dataclasses import asdict

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.graph_builder import StackGraphBuilder
from src.models import GNode

# --- GENERATOR LOGIC ---

def random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_simple_function():
    func_name = f"func_{random_string()}"
    arg_name = f"arg_{random_string()}"
    var_name = f"var_{random_string()}"
    
    code = f"""
def {func_name}({arg_name}):
    {var_name} = {arg_name}
    return {var_name}

x = {func_name}(10)
"""
    return code

def generate_class_method():
    class_name = f"Class_{random_string()}"
    method_name = f"method_{random_string()}"
    attr_name = f"attr_{random_string()}"
    
    code = f"""
class {class_name}:
    def {method_name}(self, {attr_name}):
        self.val = {attr_name}
        return self.val

obj = {class_name}()
res = obj.{method_name}(20)
"""
    return code

def generate_nested_scopes():
    outer = f"outer_{random_string()}"
    inner = f"inner_{random_string()}"
    var = f"v_{random_string()}"
    
    code = f"""
def {outer}():
    {var} = 1
    def {inner}():
        return {var}
    return {inner}()
"""
    return code

GENERATORS = [
    generate_simple_function,
    generate_class_method,
    generate_nested_scopes
]

# --- DUMP LOGIC ---

def dump_node(node: GNode, indent: int = 0):
    indent_str = "  " * indent
    print(f"{indent_str}- Type: {node.type}")
    print(f"{indent_str}  Symbol: {node.symbol}")
    print(f"{indent_str}  Range: {node.start_byte}-{node.end_byte}")
    print(f"{indent_str}  Context: {node.ctx}")
    if node.children:
        print(f"{indent_str}  Children:")
        for child in node.children:
            dump_node(child, indent + 1)

def main():
    mode = "random"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if mode == "all":
        codes = [gen() for gen in GENERATORS]
    else:
        codes = [random.choice(GENERATORS)()]

    builder = StackGraphBuilder("python")

    for i, code in enumerate(codes):
        print(f"\n{'='*20} PRODUCED TEST CASE {i+1} {'='*20}\n")
        print("### SOURCE CODE ###")
        print(code.strip())
        print("\n### STACK GRAPH ###")
        
        try:
            roots = builder.build_from_code(code)
            for root in roots:
                dump_node(root)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
