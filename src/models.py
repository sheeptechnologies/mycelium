from dataclasses import dataclass, field
from typing import List, Optional


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
    
    