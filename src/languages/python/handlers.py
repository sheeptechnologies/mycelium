import logging
from typing import Any
from ...models import GNode
from ...graph import GraphBuilder

PY_TYPES = ['str','int','float','bool','list','tuple','dict','set','NoneType']

logger = logging.getLogger(__name__)

# ================================================
# ============== MODULE ==========================   
# ================================================

def link_children(parent: GNode, children: list[GNode]):
    """Helper to link children to their parent node."""
    if not children:
        return
    for child in children:
        child.parent.append(parent)

def handle_module(builder:GraphBuilder, node:Any, children:list[GNode]):

    module_node = GNode(
        symbol="module",
        type=node.type,
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )
    link_children(module_node, children)
    return module_node
 

def handle_identifier(builder:GraphBuilder, node:Any, children:list[GNode]):
        
    return GNode(
        symbol=node.text.decode('utf-8'),
        type='POP',
        ctx="identifier",
        start_byte=node.start_byte,
        end_byte=node.end_byte, 
    )



# ====================================================
# =============== CLASS DEFINITION ===================  
# ====================================================

def handle_class_definition(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    name_field = node.child_by_field_name("name")
    body_field = node.child_by_field_name("body")
    
    if not name_field:
        logger.error(f"Class definition missing name field at {node.start_byte}")
        return None
    
    name = node_in_byte_range(name_field.byte_range, children or [])
    body_nodes = []
    if body_field:
        body_nodes = nodes_in_byte_range(body_field.byte_range, children or [])
    
    if not name:
        logger.error(f"Class name not found in children at {node.start_byte}")
        return None
    
    if not hasattr(name, 'ctx') or name.ctx != 'identifier':
        logger.error(f"Malformed class at {node.start_byte}")
        return None
    
    name_node, scope_node = _handle_class_name(builder, name)

    superclasses_field = node.child_by_field_name("superclasses")
    if superclasses_field:
        superclasses = node_in_byte_range(superclasses_field.byte_range, children or [])
        if superclasses:
            superclass_dot_node = _handle_class_superclasses(builder, superclasses)
            if superclass_dot_node:
                scope_node.children.append(superclass_dot_node)
                superclass_dot_node.parent.append(scope_node)

    scope_node.children += body_nodes
    for n in body_nodes:
        n.parent.append(scope_node)

    class_scope = GNode(
        symbol="class_scope",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=[name_node]
    )
    
    name_node.parent.append(class_scope)

    return class_scope

def _hande_class_self(class_scope: GNode):
    # POP
    self_pop_node = GNode(
        symbol="self",
        type="POP",
        start_byte=class_scope.start_byte,
        end_byte=class_scope.end_byte,
        parent=[class_scope]
    )
    class_scope.children.append(self_pop_node)
    dot_pop_node = GNode(
        symbol=".",
        type="POP",
        start_byte=class_scope.start_byte,
        end_byte=class_scope.end_byte,
        parent=[self_pop_node],
        children=[class_scope]
    )
    self_pop_node.children.append(dot_pop_node)

    

    # PUSH
    self_push_dot = GNode(
        symbol=".",
        type="PUSH",
        start_byte=class_scope.start_byte,
        end_byte=class_scope.end_byte,
        parent=[class_scope]
    )
    class_scope.children.append(self_push_dot)
    self_push_node = GNode(
        symbol="self",
        type="PUSH",
        start_byte=class_scope.start_byte,
        end_byte=class_scope.end_byte,
        parent=[self_push_dot],
        children=[class_scope]
    )
    self_push_dot.children.append(self_push_node)

def _handle_class_name(builder:GraphBuilder, name_node:GNode, children:list[GNode]=None):

    name_node.type = 'POP'

    class_braket = GNode(
        symbol='()',
        type="POP",
        ctx="class_name_braket",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte, 
        parent=[name_node],
    )
    name_node.children.append(class_braket)

    class_dot = GNode(
        symbol='.',
        type="POP",
        ctx="class_name_dot",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte, 
        parent=[name_node,class_braket]
    )
    name_node.children.append(class_dot)
    class_braket.children.append(class_dot)

    class_scope = GNode(
        symbol="class_body_scope",
        type="SCOPE",
        ctx="class_body_scope",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte,
        parent=[class_dot],
        children=[]
    )
    class_dot.children.append(class_scope)

    _hande_class_self(class_scope)
    return name_node,class_scope

def _handle_class_superclasses(builder:GraphBuilder, name_node:Any, children:list[GNode]=None):
    if not name_node:
        return None
    
    name_node.type = 'PUSH'

    class_braket = GNode(
        symbol='()',
        type="PUSH",
        ctx="class_name_braket",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte, 
        parent=[name_node],
    )
    name_node.children.append(class_braket)

    class_dot = GNode(
        symbol='.',
        type="PUSH",
        ctx="class_name_dot",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte, 
        parent=[name_node,class_braket]
    )
    name_node.children.append(class_dot)
    class_braket.children.append(class_dot)

    if builder.root_nodes and len(builder.root_nodes) > 0:
        builder.root_nodes[0].children.append(name_node)
        name_node.children.append(builder.root_nodes[0])

    return class_dot
    
# # ====================================================
# # =============== FUNCTION DEFINITION ================
# # ====================================================

def handle_function_definition(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    name_field = node.child_by_field_name("name")
    body_field = node.child_by_field_name("body")
    
    if not name_field:
        logger.warning(f"Function definition missing name field at {node.start_byte}")
        return GNode(
            symbol="function_definition",
            type="SCOPE",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    name = node_in_byte_range(name_field.byte_range, children or [])
    body = []
    if body_field:
        body = nodes_in_byte_range(body_field.byte_range, children or [])
    
    if not name:
        logger.warning(f"Function name not found in children at {node.start_byte}")
        return GNode(
            symbol="function_definition",
            type="SCOPE",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    name_node, scope_node = _handle_function_name(builder, name)
    
    function_node = GNode(
        symbol="function_definition",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=[name_node] + body
    )
    name_node.parent.append(function_node)
    link_children(function_node, body)

    parameters_field = node.child_by_field_name("parameters")
    if parameters_field:
        parameters = nodes_in_byte_range(parameters_field.byte_range, children or [])
        if parameters:
            function_node.children += parameters
            link_children(function_node, parameters)

    return_type_field = node.child_by_field_name("return_type")
    if return_type_field:
        return_type = node_in_byte_range(return_type_field.byte_range, children or [])
        if return_type:
            function_node.children.append(return_type)
            return_type.type = 'PUSH'
            link_children(function_node, [return_type])
    
    return function_node

def handle_return_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    
    for c in children:
        if c.ctx == 'identifier':
            c.type = 'PUSH'

    return children

def handle_typed_default_parameter(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    if not children or len(children) < 2:
        logger.warning(f"typed_default_parameter requires at least 2 children, got {len(children) if children else 0}")
        return children or []
    
    name_node = children[0] 
    type_node = children[1]
    value_node = children[2] if len(children) > 2 else None

    if name_node:
        name_node.type = 'POP'
        res = [name_node]
    else:
        res = []
    
    if type_node:
        type_node.type = 'PUSH'
        if not type_node.symbol in PY_TYPES:
            res += [type_node]

    if value_node:
        value_node.type = 'PUSH'
        res += [value_node]
    
    return res

def handle_typed_parameter(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    if not children or len(children) < 2:
        logger.warning(f"typed_parameter requires at least 2 children, got {len(children) if children else 0}")
        return children or []
    
    name_node = children[0]  # identifier
    type_node = children[1]
    
    if not name_node or not type_node:
        return children or []
    
    res = []
    name_node.type = 'POP'
    type_node.type = 'PUSH'

    if type_node.symbol in PY_TYPES:
        return [name_node]
    
    return [name_node, type_node]

def _handle_function_name(builder:GraphBuilder, name_node:GNode, children:list[GNode]=None):

    name_node.type = 'POP'

    func_braket = GNode(
        symbol='()',
        type="POP",
        ctx="function_name_braket",
        start_byte=name_node.start_byte,
        end_byte=name_node.end_byte, 
        parent=[name_node],
    )
    name_node.children.append(func_braket)


    return name_node,func_braket

# # ==========================================================================
# # =============== expression_statement_assignment ==========================   
# # ==========================================================================

def handle_expression_statement_assignment(builder:GraphBuilder, node:Any, children:list[GNode]=None):

    expr_scope = GNode(
        symbol="expression_statement_assignment",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )
    link_children(expr_scope, children)
    return expr_scope

def handle_assignment(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    left_node_field = node.child_by_field_name("left")
    right_node_field = node.child_by_field_name("right")
    
    left = []
    right = []
    
    if left_node_field:
        left = nodes_in_byte_range(left_node_field.byte_range, children or [])
    if right_node_field:
        right = nodes_in_byte_range(right_node_field.byte_range, children or [])

    if right:
        propagate_type(right, 'PUSH')

    if left:
        propagate_type(left, 'POP')

    for nr in right:
        for nl in left:
            if hasattr(nr, 'ctx') and nr.ctx == 'call':
                def find_call_braket_node(node):
                    for n in node.children:
                        if hasattr(n, 'ctx') and n.ctx == 'call_braket':
                            return n
                        if n.children:
                            result = find_call_braket_node(n)
                            if result:
                                return result
                    return None

                call_braket = find_call_braket_node(nr)
                if call_braket:
                    append_in_graph(nl, call_braket)

    res = left + right
    return [x for x in res if x is not None]


# ==========================================================================
# ============================= call =======================================   
# ==========================================================================

def handle_call(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    if children:
        propagate_type(children, 'PUSH')
    
    function_node = node.child_by_field_name("function")
    if not function_node:
        logger.warning(f"call node missing function field at {node.start_byte}")
        return GNode(
            symbol="call",
            type="SCOPE",
            ctx="call",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    function = node_in_byte_range(function_node.byte_range, children or [])
    if not function:
        logger.warning(f"call function not found in children at {node.start_byte}")
        return GNode(
            symbol="call",
            type="SCOPE",
            ctx="call",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    function.ctx = 'call_name'
    x = function
    while x and len(x.children) > 0:
        x = x.children[0]

    if x:
        x.children.append(GNode(
            symbol="()",
            type="PUSH",
            ctx="call_braket",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
        ))
    
    arguments_node = node.child_by_field_name("arguments")
    arguments = []
    if arguments_node:
        arguments = nodes_in_byte_range(arguments_node.byte_range, children or [])

    call_children = [function] + arguments

    call_node = GNode(
        symbol="call",
        type="SCOPE",
        ctx="call",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=call_children
    )
    link_children(call_node, call_children)
    return call_node

def append_in_graph(root,node):
    
    leaves = []
    visited = set()
    def get_leaves(root):
        if id(root) in visited:
            return
        visited.add(id(root))

        if not root.children:
            leaves.append(root)
            return
        for c in root.children:
            get_leaves(c)

    get_leaves(root)
    for leaf in leaves:
        leaf.children.append(node)
        node.parent.append(leaf)


def handle_attribute(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    if children:
        propagate_type(children, 'PUSH')
    
    object_node_field = node.child_by_field_name("object")
    attribute_node_field = node.child_by_field_name("attribute")
    
    if not object_node_field or not attribute_node_field:
        logger.warning(f"attribute node missing object or attribute field at {node.start_byte}")
        return GNode(
            symbol="attribute",
            type="SCOPE",
            ctx="attribute",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    object = node_in_byte_range(object_node_field.byte_range, children or [])
    attribute = node_in_byte_range(attribute_node_field.byte_range, children or [])
    
    if not object or not attribute:
        logger.warning(f"attribute: object or attribute not found in children at {node.start_byte}")
        return object or attribute or GNode(
            symbol="attribute",
            type="SCOPE",
            ctx="attribute",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )

    n = GNode(
        symbol=".",
        ctx="attribute_dot",
        type="PUSH",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=[attribute]
    )

    if hasattr(object, 'ctx') and object.ctx == 'identifier':
        append_in_graph(object, n)
        return object
    elif hasattr(object, 'ctx') and object.ctx == 'call':
        object_children = []
        object_node = None
        for c in object.children:
            if hasattr(c, 'ctx') and c.ctx == 'call_name':
                object_node = c
            else: 
                object_children.append(c)
        
        if object_node:
            x = object_node
            while x and len(x.children) > 0:
                x = x.children[0]
            
            if x:
                x.children.append(n)
            
            return [object_node] + object_children
    
    return object


def handle_lambda(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    
    return GNode(
        symbol="lambda",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )

def propagate_type(start_nodes: list[GNode], new_type: str):
    """
    Attraversa il grafo partendo da start_nodes e imposta 'new_type'
    su tutti i nodi identificatori raggiungibili.
    Gestisce correttamente i cicli usando un set di visitati.
    """
    if not start_nodes:
        return

    # 1. Il Set per evitare i cicli (tracciamo l'id univoco dell'oggetto in memoria)
    visited = set()
    
    # 2. Lo Stack per la visita (DFS iterativa)
    # Copiamo la lista iniziale per non modificare quella del chiamante
    stack = list(start_nodes)

    while stack:
        current_node = stack.pop()

        if(current_node is None):
            continue
    
        # Se abbiamo già visto questo nodo, saltiamo per evitare loop
        if id(current_node) in visited:
            continue
        
        # Marchiamo come visitato
        visited.add(id(current_node))

        # 3. LOGICA DI APPLICAZIONE (Solo per Identifier)
        # Qui controlliamo se è un identifier. 
        # Adatta la stringa 'identifier' se nel tuo ctx usi altro (es. 'RAW_ID')
        if current_node.type != "SCOPE": 
            current_node.type = new_type

        # 4. PROPAGAZIONE
        # Aggiungiamo tutti i figli allo stack per continuare la discesa
        if current_node.children:
            stack.extend(current_node.children)

def node_in_byte_range(range, nodes):
    """Find a node within the given byte range."""
    if not range or not nodes:
        return None
    
    try:
        range_start, range_end = range[0], range[1]
    except (IndexError, TypeError):
        return None
    
    for n in nodes:
        if n and hasattr(n, 'start_byte') and hasattr(n, 'end_byte'):
            if n.start_byte >= range_start and n.end_byte <= range_end:
                return n

    return None

def nodes_in_byte_range(range, nodes):
    """Find all nodes within the given byte range."""
    if not range or not nodes:
        return []
    
    try:
        range_start, range_end = range[0], range[1]
    except (IndexError, TypeError):
        return []
    
    res = []
    for n in nodes:
        if n and hasattr(n, 'start_byte') and hasattr(n, 'end_byte'):
            if n.start_byte >= range_start and n.end_byte <= range_end:
                res.append(n)

    return res

# ==========================================================================
# ============================= IMPORTS ====================================
# ==========================================================================

def handle_import_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: import module.submodule
    Creates PUSH chain for module path and POP for root module name definition.
    """
    name_node = node.child_by_field_name("name")
    if not name_node:
        logger.warning(f"import_statement missing name field at {node.start_byte}")
        return GNode(
            symbol="import_statement",
            type="SCOPE",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    # Find dotted_name in children
    dotted_name_node = node_in_byte_range(name_node.byte_range, children or [])
    
    # Create import scope
    import_scope = GNode(
        symbol="import_statement",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    
    return import_scope

def handle_import_from_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: from module import name
    Creates PUSH chain for module path and POP for imported name definition.
    """
    import_scope = GNode(
        symbol="import_from_statement",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    
    return import_scope

def handle_dotted_name(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: module.submodule.name
    Creates chain of PUSH nodes connected by dots.
    """
    # Extract identifiers from dotted_name
    identifiers = []
    current = node
    while current:
        if current.type == "identifier":
            identifiers.append(current)
        current = current.next_sibling if hasattr(current, 'next_sibling') else None
    
    if not identifiers:
        return None
    
    # Create chain: name -> . -> parent -> . -> grandparent -> root
    result_nodes = []
    prev_node = None
    
    for i, ident_node in enumerate(identifiers):
        ident_text = ident_node.text.decode('utf-8') if hasattr(ident_node, 'text') else ""
        
        # Find corresponding child node
        ident_gnode = node_in_byte_range(ident_node.byte_range, children or [])
        if not ident_gnode:
            ident_gnode = GNode(
                symbol=ident_text,
                type="PUSH",
                ctx="identifier",
                start_byte=ident_node.start_byte,
                end_byte=ident_node.end_byte
            )
        
        ident_gnode.type = "PUSH"
        result_nodes.append(ident_gnode)
        
        # Add dot node between identifiers (except for the last one)
        if i < len(identifiers) - 1:
            dot_node = GNode(
                symbol=".",
                type="PUSH",
                ctx="dotted_name_dot",
                start_byte=ident_node.end_byte,
                end_byte=identifiers[i+1].start_byte if i+1 < len(identifiers) else ident_node.end_byte
            )
            ident_gnode.children.append(dot_node)
            dot_node.parent.append(ident_gnode)
            if prev_node:
                dot_node.children.append(prev_node)
                prev_node.parent.append(dot_node)
            prev_node = ident_gnode
        else:
            if prev_node:
                ident_gnode.children.append(prev_node)
                prev_node.parent.append(ident_gnode)
    
    return result_nodes[0] if result_nodes and len(result_nodes) > 0 else None

def handle_aliased_import(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: import module as alias
    Creates definition for alias pointing to imported name.
    """
    alias_node = node.child_by_field_name("alias")
    name_node = node.child_by_field_name("name")
    
    if not alias_node:
        logger.warning(f"aliased_import missing alias field at {node.start_byte}")
        return GNode(
            symbol="aliased_import",
            type="SCOPE",
            ctx="aliased_import",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=children or []
        )
    
    # Find alias identifier in children
    alias_gnode = node_in_byte_range(alias_node.byte_range, children or [])
    if alias_gnode:
        alias_gnode.type = "POP"
        alias_gnode.ctx = "aliased_import"
        return alias_gnode
    
    # Return a placeholder if not found
    return GNode(
        symbol="aliased_import",
        type="POP",
        ctx="aliased_import",
        start_byte=alias_node.start_byte,
        end_byte=alias_node.end_byte
    )

def handle_relative_import(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: from .module import name or from ..module import name
    Creates reference to parent/grandparent module.
    """
    prefix_node = node.child_by_field_name("prefix")
    
    relative_scope = GNode(
        symbol="relative_import",
        type="SCOPE",
        ctx="relative_import",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    
    return relative_scope

def handle_wildcard_import(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: from module import *
    Creates wildcard import node.
    """
    wildcard_node = GNode(
        symbol="*",
        type="PUSH",
        ctx="wildcard_import",
        start_byte=node.start_byte,
        end_byte=node.end_byte
    )
    
    return wildcard_node

def handle_import_prefix(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: . or .. in relative imports
    """
    prefix_text = node.text.decode('utf-8') if hasattr(node, 'text') else ""
    
    prefix_node = GNode(
        symbol=prefix_text,
        type="PUSH",
        ctx="import_prefix",
        start_byte=node.start_byte,
        end_byte=node.end_byte
    )
    
    return prefix_node

# ==========================================================================
# ============================= DECORATORS ================================
# ==========================================================================

def handle_decorated_definition(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: @decorator def func(): or @decorator class MyClass:
    Wraps the definition with decorator scope.
    """
    definition_node = node.child_by_field_name("definition")
    decorators = []
    
    # Find decorator nodes in children
    if children:
        for child in children:
            if hasattr(child, 'ctx') and child.ctx == 'decorator':
                decorators.append(child)
    
    decorated_scope = GNode(
        symbol="decorated_definition",
        type="SCOPE",
        ctx="decorated_definition",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=decorators + (children or [])
    )
    link_children(decorated_scope, decorators + (children or []))
    return decorated_scope

def handle_decorator(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: @decorator
    Creates decorator reference node.
    """
    decorator_node = GNode(
        symbol="decorator",
        type="PUSH",
        ctx="decorator",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(decorator_node, children or [])
    return decorator_node

# ==========================================================================
# ============================= CONTROL FLOW ==============================
# ==========================================================================

def handle_if_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: if condition: ... elif: ... else: ...
    Creates scope for each branch.
    """
    if_scope = GNode(
        symbol="if_statement",
        type="SCOPE",
        ctx="if_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(if_scope, children or [])
    return if_scope

def handle_elif_clause(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: elif condition:
    Creates scope for elif branch.
    """
    elif_scope = GNode(
        symbol="elif_clause",
        type="SCOPE",
        ctx="elif_clause",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(elif_scope, children or [])
    return elif_scope

def handle_else_clause(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: else:
    Creates scope for else branch.
    """
    else_scope = GNode(
        symbol="else_clause",
        type="SCOPE",
        ctx="else_clause",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(else_scope, children or [])
    return else_scope

def handle_for_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: for item in iterable:
    Creates scope for loop body and loop variable definition.
    """
    # Find loop variable (left side of 'in')
    left_node = node.child_by_field_name("left")
    right_node = node.child_by_field_name("right")
    body_node = node.child_by_field_name("body")
    
    # Mark loop variable as POP (definition)
    if left_node and children:
        left_nodes = nodes_in_byte_range(left_node.byte_range, children)
        for left in left_nodes:
            if hasattr(left, 'ctx') and left.ctx == 'identifier':
                left.type = 'POP'
    
    for_scope = GNode(
        symbol="for_statement",
        type="SCOPE",
        ctx="for_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(for_scope, children or [])
    return for_scope

def handle_while_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: while condition:
    Creates scope for while loop body.
    """
    while_scope = GNode(
        symbol="while_statement",
        type="SCOPE",
        ctx="while_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(while_scope, children or [])
    return while_scope

def handle_match_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: match value: case pattern: (Python 3.10+)
    Creates scope for match statement.
    """
    match_scope = GNode(
        symbol="match_statement",
        type="SCOPE",
        ctx="match_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(match_scope, children or [])
    return match_scope

def handle_case_clause(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: case pattern:
    Creates scope for case clause with pattern binding.
    """
    case_scope = GNode(
        symbol="case_clause",
        type="SCOPE",
        ctx="case_clause",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(case_scope, children or [])
    return case_scope

# ==========================================================================
# ============================= EXCEPTIONS ================================
# ==========================================================================

def handle_try_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: try: ... except: ... finally: ...
    Creates scope for try, except, and finally blocks.
    """
    try_scope = GNode(
        symbol="try_statement",
        type="SCOPE",
        ctx="try_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(try_scope, children or [])
    return try_scope

def handle_except_clause(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: except Exception as e:
    Creates scope for except block and binds exception variable.
    """
    # Find exception variable (as e)
    exception_node = node.child_by_field_name("exception")
    if exception_node and children:
        exception_nodes = nodes_in_byte_range(exception_node.byte_range, children)
        for exc in exception_nodes:
            if hasattr(exc, 'ctx') and exc.ctx == 'identifier':
                exc.type = 'POP'  # Exception variable is defined
    
    except_scope = GNode(
        symbol="except_clause",
        type="SCOPE",
        ctx="except_clause",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(except_scope, children or [])
    return except_scope

def handle_finally_clause(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: finally:
    Creates scope for finally block.
    """
    finally_scope = GNode(
        symbol="finally_clause",
        type="SCOPE",
        ctx="finally_clause",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(finally_scope, children or [])
    return finally_scope

def handle_raise_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: raise Exception
    Creates reference to exception.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    raise_node = GNode(
        symbol="raise_statement",
        type="SCOPE",
        ctx="raise_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(raise_node, children or [])
    return raise_node

# ==========================================================================
# ============================= CONTEXT MANAGERS ==========================
# ==========================================================================

def handle_with_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: with context_manager as var:
    Creates scope for with block and binds context variable.
    """
    with_scope = GNode(
        symbol="with_statement",
        type="SCOPE",
        ctx="with_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(with_scope, children or [])
    return with_scope

def handle_with_item(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: context_manager as var in with statement
    Binds context variable.
    """
    # Find alias (as var)
    alias_node = node.child_by_field_name("alias")
    if alias_node and children:
        alias_nodes = nodes_in_byte_range(alias_node.byte_range, children)
        for alias in alias_nodes:
            if hasattr(alias, 'ctx') and alias.ctx == 'identifier':
                alias.type = 'POP'  # Context variable is defined
    
    with_item_node = GNode(
        symbol="with_item",
        type="SCOPE",
        ctx="with_item",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(with_item_node, children or [])
    return with_item_node

# ==========================================================================
# ============================= STATEMENTS ================================
# ==========================================================================

def handle_global_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: global var1, var2
    Marks variables as global.
    """
    global_scope = GNode(
        symbol="global_statement",
        type="SCOPE",
        ctx="global_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(global_scope, children or [])
    return global_scope

def handle_nonlocal_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: nonlocal var1, var2
    Marks variables as nonlocal.
    """
    nonlocal_scope = GNode(
        symbol="nonlocal_statement",
        type="SCOPE",
        ctx="nonlocal_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(nonlocal_scope, children or [])
    return nonlocal_scope

def handle_break_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: break
    Simple statement node.
    """
    return GNode(
        symbol="break",
        type="SCOPE",
        ctx="break_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte
    )

def handle_continue_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: continue
    Simple statement node.
    """
    return GNode(
        symbol="continue",
        type="SCOPE",
        ctx="continue_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte
    )

def handle_delete_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: del var
    Creates reference to deleted variable.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    del_node = GNode(
        symbol="delete_statement",
        type="SCOPE",
        ctx="delete_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(del_node, children or [])
    return del_node

def handle_assert_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: assert condition
    Creates reference to assertion.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    assert_node = GNode(
        symbol="assert_statement",
        type="SCOPE",
        ctx="assert_statement",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(assert_node, children or [])
    return assert_node

# ==========================================================================
# ============================= DATA STRUCTURES ===========================
# ==========================================================================

def handle_tuple(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: (a, b, c) or a, b, c
    Creates tuple node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    tuple_node = GNode(
        symbol="tuple",
        type="SCOPE",
        ctx="tuple",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(tuple_node, children or [])
    return tuple_node

def handle_list(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: [a, b, c]
    Creates list node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    list_node = GNode(
        symbol="list",
        type="SCOPE",
        ctx="list",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(list_node, children or [])
    return list_node

def handle_dictionary(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: {key: value, ...}
    Creates dictionary node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    dict_node = GNode(
        symbol="dictionary",
        type="SCOPE",
        ctx="dictionary",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(dict_node, children or [])
    return dict_node

def handle_set(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: {a, b, c}
    Creates set node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    set_node = GNode(
        symbol="set",
        type="SCOPE",
        ctx="set",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(set_node, children or [])
    return set_node

def handle_pair(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: key: value in dictionary
    Creates pair node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    pair_node = GNode(
        symbol="pair",
        type="SCOPE",
        ctx="pair",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(pair_node, children or [])
    return pair_node

def handle_list_comprehension(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: [x for x in iterable]
    Creates comprehension scope.
    """
    comp_scope = GNode(
        symbol="list_comprehension",
        type="SCOPE",
        ctx="list_comprehension",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(comp_scope, children or [])
    return comp_scope

def handle_dictionary_comprehension(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: {k: v for k, v in iterable}
    Creates comprehension scope.
    """
    comp_scope = GNode(
        symbol="dictionary_comprehension",
        type="SCOPE",
        ctx="dictionary_comprehension",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(comp_scope, children or [])
    return comp_scope

def handle_set_comprehension(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: {x for x in iterable}
    Creates comprehension scope.
    """
    comp_scope = GNode(
        symbol="set_comprehension",
        type="SCOPE",
        ctx="set_comprehension",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(comp_scope, children or [])
    return comp_scope

def handle_generator_expression(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: (x for x in iterable)
    Creates generator scope.
    """
    gen_scope = GNode(
        symbol="generator_expression",
        type="SCOPE",
        ctx="generator_expression",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(gen_scope, children or [])
    return gen_scope

# ==========================================================================
# ============================= EXPRESSIONS ================================
# ==========================================================================

def handle_subscript(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: obj[index] or obj[start:end]
    Creates subscript reference.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    subscript_node = GNode(
        symbol="subscript",
        type="SCOPE",
        ctx="subscript",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(subscript_node, children or [])
    return subscript_node

def handle_binary_operator(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: a + b, a - b, etc.
    Creates binary operator node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="binary_operator",
        type="SCOPE",
        ctx="binary_operator",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_unary_operator(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: -a, +a, not a, etc.
    Creates unary operator node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="unary_operator",
        type="SCOPE",
        ctx="unary_operator",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_comparison_operator(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: a == b, a < b, etc.
    Creates comparison node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="comparison_operator",
        type="SCOPE",
        ctx="comparison_operator",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_boolean_operator(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: a and b, a or b
    Creates boolean operator node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="boolean_operator",
        type="SCOPE",
        ctx="boolean_operator",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_conditional_expression(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: x if condition else y
    Creates ternary operator node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="conditional_expression",
        type="SCOPE",
        ctx="conditional_expression",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_named_expression(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: (x := value) - walrus operator
    Creates assignment and reference.
    """
    # Find name in children
    if children:
        for child in children:
            if hasattr(child, 'ctx') and child.ctx == 'identifier':
                child.type = 'POP'  # Assignment
    
    op_node = GNode(
        symbol="named_expression",
        type="SCOPE",
        ctx="named_expression",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_list_splat(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: *args
    Creates splat node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="*",
        type="PUSH",
        ctx="list_splat",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_dictionary_splat(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: **kwargs
    Creates dictionary splat node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    op_node = GNode(
        symbol="**",
        type="PUSH",
        ctx="dictionary_splat",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(op_node, children or [])
    return op_node

def handle_expression_list(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: a, b, c (comma-separated expressions)
    Creates expression list node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    expr_list = GNode(
        symbol="expression_list",
        type="SCOPE",
        ctx="expression_list",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(expr_list, children or [])
    return expr_list

# ==========================================================================
# ============================= PATTERN MATCHING ==========================
# ==========================================================================

def handle_as_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: pattern as alias (Python 3.10+)
    Creates pattern binding.
    """
    # Find alias in children
    alias_node = node.child_by_field_name("alias")
    if alias_node and children:
        alias_nodes = nodes_in_byte_range(alias_node.byte_range, children)
        for alias in alias_nodes:
            if hasattr(alias, 'ctx') and alias.ctx == 'identifier':
                alias.type = 'POP'  # Pattern variable is defined
    
    as_pat = GNode(
        symbol="as_pattern",
        type="SCOPE",
        ctx="as_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(as_pat, children or [])
    return as_pat

def handle_tuple_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: (a, b, c) pattern
    Creates tuple pattern node.
    """
    tup_pat = GNode(
        symbol="tuple_pattern",
        type="SCOPE",
        ctx="tuple_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(tup_pat, children or [])
    return tup_pat

def handle_list_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: [a, b, c] pattern
    Creates list pattern node.
    """
    list_pat = GNode(
        symbol="list_pattern",
        type="SCOPE",
        ctx="list_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(list_pat, children or [])
    return list_pat

def handle_dict_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: {key: value} pattern
    Creates dict pattern node.
    """
    dict_pat = GNode(
        symbol="dict_pattern",
        type="SCOPE",
        ctx="dict_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(dict_pat, children or [])
    return dict_pat

def handle_class_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: ClassName(...) pattern
    Creates class pattern node.
    """
    cls_pat = GNode(
        symbol="class_pattern",
        type="SCOPE",
        ctx="class_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(cls_pat, children or [])
    return cls_pat

def handle_splat_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: *pattern
    Creates splat pattern node.
    """
    splat = GNode(
        symbol="splat_pattern",
        type="SCOPE",
        ctx="splat_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(splat, children or [])
    return splat

def handle_union_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: pattern1 | pattern2
    Creates union pattern node.
    """
    union_pat = GNode(
        symbol="union_pattern",
        type="SCOPE",
        ctx="union_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(union_pat, children or [])
    return union_pat

def handle_keyword_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: key=pattern
    Creates keyword pattern node.
    """
    kw_pat = GNode(
        symbol="keyword_pattern",
        type="SCOPE",
        ctx="keyword_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(kw_pat, children or [])
    return kw_pat

def handle_case_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: case pattern in match statement
    Creates case pattern node.
    """
    case_pat = GNode(
        symbol="case_pattern",
        type="SCOPE",
        ctx="case_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(case_pat, children or [])
    return case_pat

def handle_pattern_list(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: pattern1, pattern2, ...
    Creates pattern list node.
    """
    pat_list = GNode(
        symbol="pattern_list",
        type="SCOPE",
        ctx="pattern_list",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(pat_list, children or [])
    return pat_list

# ==========================================================================
# ============================= ADVANCED PARAMETERS =======================
# ==========================================================================

def handle_default_parameter(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: param=default_value
    Creates parameter with default value.
    """
    if children and len(children) >= 2:
        # First child is parameter name (POP), second is default value (PUSH)
        children[0].type = 'POP'
        propagate_type([children[1]], 'PUSH')
    
    dp_node = GNode(
        symbol="default_parameter",
        type="SCOPE",
        ctx="default_parameter",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(dp_node, children or [])
    return dp_node

def handle_list_splat_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: *args in function parameters
    Creates splat parameter node.
    """
    if children:
        for child in children:
            if hasattr(child, 'ctx') and child.ctx == 'identifier':
                child.type = 'POP'  # Parameter is defined
    
    node_splat = GNode(
        symbol="*",
        type="POP",
        ctx="list_splat_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(node_splat, children or [])
    return node_splat

def handle_dictionary_splat_pattern(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: **kwargs in function parameters
    Creates dictionary splat parameter node.
    """
    if children:
        for child in children:
            if hasattr(child, 'ctx') and child.ctx == 'identifier':
                child.type = 'POP'  # Parameter is defined
    
    node_splat = GNode(
        symbol="**",
        type="POP",
        ctx="dictionary_splat_pattern",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(node_splat, children or [])
    return node_splat

def handle_lambda_parameters(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: lambda x, y: ...
    Creates lambda parameters scope.
    """
    lp_scope = GNode(
        symbol="lambda_parameters",
        type="SCOPE",
        ctx="lambda_parameters",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(lp_scope, children or [])
    return lp_scope

def handle_argument_list(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: func(arg1, arg2, ...)
    Creates argument list node.
    """
    if children:
        propagate_type(children, 'PUSH')
    
    arg_list_scope = GNode(
        symbol="argument_list",
        type="SCOPE",
        ctx="argument_list",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(arg_list_scope, children or [])
    return arg_list_scope

def handle_keyword_argument(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: func(keyword=value)
    Creates keyword argument node.
    """
    if children and len(children) >= 2:
        # First is keyword name, second is value
        propagate_type([children[1]], 'PUSH')
    
    kw_arg = GNode(
        symbol="keyword_argument",
        type="SCOPE",
        ctx="keyword_argument",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(kw_arg, children or [])
    return kw_arg

# ==========================================================================
# ============================= BLOCKS ====================================
# ==========================================================================

def handle_block(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    """
    Handle: code block (indented block)
    Creates block scope.
    """
    block_node = GNode(
        symbol="block",
        type="SCOPE",
        ctx="block",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children or []
    )
    link_children(block_node, children or [])
    return block_node