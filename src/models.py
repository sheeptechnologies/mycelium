from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class GNode:
    symbol: str
    type: str
    start_byte: int
    end_byte: int

    children: List['GNode'] = field(default_factory=list)
    parent: List['GNode'] = field(default_factory=list) 
    ctx: str = field(default="PUSH")

    def __repr__(self):
        return f"{self.type}:{self.symbol} - ({self.start_byte}, {self.end_byte})"


@dataclass
class ResolutionResult:
    """Risultato di una risoluzione di riferimento."""
    definition: GNode  # Il nodo POP trovato
    path: List[GNode]  # Il percorso dal riferimento alla definizione
    confidence: float = 1.0  # Livello di confidenza (0.0-1.0)
    
    def __repr__(self):
        return f"ResolutionResult(definition={self.definition.symbol}, path_length={len(self.path)}, confidence={self.confidence})"


@dataclass
class ResolutionState:
    """Stato interno durante la risoluzione."""
    current_node: GNode
    symbol_stack: List[str]  # Stack di simboli da risolvere
    scope_stack: List[GNode]  # Stack di scope attivi
    path: List[GNode]  # Path percorso finora
    visited: Set[int]  # Nodi visitati (per evitare cicli)
    
    def __repr__(self):
        return f"ResolutionState(node={self.current_node.symbol}, symbol_stack={len(self.symbol_stack)}, scope_stack={len(self.scope_stack)}, path_length={len(self.path)})"
    
    