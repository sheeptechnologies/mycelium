from typing import Any, List, Dict
from tree_sitter import Node
from .models import GNode
# Assumo che GNode sia importato correttamente

class GraphBuilder:
    def __init__(self):
        self.root_node = GNode(
            symbol='source_file',
            type="SCOPE",
            ctx="source_file",
            start_byte=0,
            end_byte=0,
        )
        self.root_nodes = [self.root_node]
        self.stack: List[Dict] = [] 

    def build(self, nodes: List[tuple[Node, str]], handler_map: dict):

        for node, handler_name in  self.sort_captures(nodes):
            
            while self.stack and self.stack[-1]['node'].end_byte <= node.start_byte:
                self._process_and_pop()

            handler = handler_map.get(handler_name)
            if handler:

                ctx = {
                    'node': node,
                    'handler': handler,
                    'children_results': []  # accumuleremo figli diretti
                }
                self.stack.append(ctx)
            else: 
                print(f"[ERROR] no handler for {node.type}")
        # Flush
        while self.stack:
            self._process_and_pop()

        return self.root_nodes

    def _process_and_pop(self):
        ctx = self.stack.pop()
        node = ctx['node']
        handler = ctx['handler']
        children_results = ctx['children_results']

        result = handler(self, node, children_results)

        # Se l'handler non ritorna nulla, usciamo
        if not result:
            return

        # --- NORMALIZZAZIONE ---
        # Trasformiamo tutto in una lista per trattarlo uniformemente
        items_to_add = result if isinstance(result, list) else [result]

        # --- AGGIUNTA AL PADRE ---
        if self.stack:
            # Usiamo extend! Così [A, B] vengono aggiunti come A, B
            self.stack[-1]['children_results'].extend(items_to_add)
        else:
            # Anche qui, se è la radice, usiamo extend sui figli
            # Nota: Assumo che self.root_node sia un GNode modulo/file
            self.root_node.children.extend(items_to_add)

    def sort_captures(self,captures: List[tuple[Any, str]]) -> List[tuple[Any, str]]:
        """
        Riordina le catture per garantire che i contenitori entrino nello stack prima dei contenuti
        anche quando hanno lo stesso byte range.
        """
        
        # Definiamo una priorità per i tipi di cattura
        # Valori BASSI = Entrano PRIMA nello stack (Genitori/Contenitori)
        # Valori ALTI = Entrano DOPO nello stack (Figli/Identifier)
        PRIORITY_MAP = {
            # Contenitori logici (Bassa priorità, stanno sul fondo)
            # "attribute_object": 1,
            # "attribute_object_attribute": 1,
            # "call_function": 1,
            
            # # Elementi strutturali intermedi
            # "attribute": 1,
            # "call": 1,
            
            # Foglie concrete (Alta priorità, vengono processate subito)
            "identifier": 100,
            "string": 100,
            "number": 100
        }

        def sort_key(item):
            node, name = item
            
            # 1. Start Byte (Prima chi inizia prima)
            k1 = node.start_byte
            
            # 2. End Byte Inverso (Prima chi finisce DOPO -> Contenitore più grande)
            k2 = -node.end_byte
            
            # 3. Priorità Manuale (Se i range sono identici, usa la mappa)
            # Default 50 se non specificato
            k3 = PRIORITY_MAP.get(name, 50)
            
            return (k1, k2, k3)

        return sorted(captures, key=sort_key)