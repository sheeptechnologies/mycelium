import logging
from typing import Any
from ...models import GNode
from ...graph import GraphBuilder

PY_TYPES = ['str','int','float','bool','list','tuple','dict','set','NoneType']

logger = logging.getLogger(__name__)

# ================================================
# ============== MODULE ==========================   
# ================================================

def handle_module(builder:GraphBuilder, node:Any, children:list[GNode]):

    return GNode(
        symbol="module",
        type=node.type,
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )
 

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
    
    name = node_in_byte_range(node.child_by_field_name("name").byte_range, children)   
    body_nodes = nodes_in_byte_range(node.child_by_field_name("body").byte_range, children)
    
    if( not name.ctx == 'identifier'):
        logger.error(f"Malformed class at {node.start_byte}")
        return None
    

    
    name_node,scope_node = _handle_class_name(builder,name)

    if(node.child_by_field_name("superclasses")):
        superclasses = node_in_byte_range(node.child_by_field_name("superclasses").byte_range, children)
        if(superclasses):
            superclass_dot_node = _handle_class_superclasses(builder,superclasses)
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

    builder.root_nodes[0].children.append(name_node)
    name_node.children.append(builder.root_nodes[0])

    return class_dot
    
# # ====================================================
# # =============== FUNCTION DEFINITION ================
# # ====================================================

def handle_function_definition(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    
    name = node_in_byte_range(node.child_by_field_name("name").byte_range, children)
    body = nodes_in_byte_range(node.child_by_field_name("body").byte_range, children)
    
    name_node,scope_node = _handle_function_name(builder,name)
    
    function_node = GNode(
        symbol="function_definition",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=[name_node] + body
    )
    name_node.parent.append(function_node)

    if node.child_by_field_name("parameters"):
        parameters = nodes_in_byte_range(node.child_by_field_name("parameters").byte_range, children)
        function_node.children += parameters

    if node.child_by_field_name("return_type"):
        return_type = node_in_byte_range(node.child_by_field_name("return_type").byte_range, children)
        function_node.children.append(return_type)
        return_type.type = 'PUSH'
    
    return function_node

def handle_return_statement(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    
    for c in children:
        if c.ctx == 'identifier':
            c.type = 'PUSH'

    return children

def handle_typed_default_parameter(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    name_node = children[0] 
    type_node = children[1]
    value_node = children[2]

    name_node.type = 'POP'
    res = [name_node]
    type_node.type = 'PUSH'

    if not type_node.symbol in PY_TYPES:
        res += [type_node]

    if value_node:
        value_node.type = 'PUSH'
        res += [value_node]
    
    return res

def handle_typed_parameter(builder:GraphBuilder, node:Any, children:list[GNode]=None):
    name_node = children[0]  # identifier
    type_node = children[1]
    res = []
    name_node.type = 'POP'
    type_node.type = 'PUSH'

    if type_node in PY_TYPES:
        return [name_node]
    
    return [name_node,type_node]

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

    return GNode(
        symbol="expression_statement_assignment",
        type="SCOPE",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )

def handle_assignment(builder:GraphBuilder, node:Any, children:list[GNode]=None):

    left = nodes_in_byte_range(node.child_by_field_name("left").byte_range, children)
    right = nodes_in_byte_range(node.child_by_field_name("right").byte_range, children)

    if(right):
        propagate_type(right,'PUSH')

    propagate_type(left,'POP')

    for nr in right:
        for nl in left:
            if nr.ctx == 'call':
                def find_call_braket_node(node):
                    for n in node.children:
                        if n.ctx == 'call_braket':
                            return n
                        if n.children:
                            return find_call_braket_node(n)

                call_braket = find_call_braket_node(nr)
                append_in_graph(nl,call_braket)

            

    res = left + right
    return [x for x in res if x is not None]


# ==========================================================================
# ============================= call =======================================   
# ==========================================================================

def handle_call(builder:GraphBuilder, node:Any, children:list[GNode]=None):

    propagate_type(children,'PUSH')
    function = node_in_byte_range(node.child_by_field_name("function").byte_range, children)
    function.ctx = 'call_name'
    x = function
    while len(x.children) > 0:
        x = x.children[0]


    x.children.append(GNode(
        symbol="()",
        type="PUSH",
        ctx="call_braket",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
    ))
    
    arguments = nodes_in_byte_range(node.child_by_field_name("arguments").byte_range, children)    

    children = [function] + arguments

    return GNode(
        symbol="call",
        type="SCOPE",
        ctx="call",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=children
    )

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

    propagate_type(children,'PUSH')
    object = node_in_byte_range(node.child_by_field_name("object").byte_range, children)
    attribute = node_in_byte_range(node.child_by_field_name("attribute").byte_range, children)    

    n = GNode(
        symbol=".",
        ctx="attribute_dot",
        type="PUSH",
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        children=[attribute]
    )

    if(object.ctx == 'identifier'):
        append_in_graph(object,n)
    elif(object.ctx == 'call'):

        object_children = []
        object_node = None
        for c in object.children:
            if(c.ctx == 'call_name'):
                object_node = c
            else: 
                object_children.append(c)
        
        object = object_node

        x = object
        while len(x.children) > 0:
            x = x.children[0]
        
        x.children.append(n)

        return [object] + object_children
    
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

def node_in_byte_range(range,nodes):

    for n in nodes:
        if(n.start_byte >= range[0] and n.end_byte <= range[1]):
            return n

    return None

def nodes_in_byte_range(range,nodes):

    res = []
    for n in nodes:
        if(n.start_byte >= range[0] and n.end_byte <= range[1]):
            res.append(n)

    return res