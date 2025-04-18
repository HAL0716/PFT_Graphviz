from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Node:
    label: str = ""
    phase: int = 0

    def __repr__(self) -> str:
        return f"({self.label}, {self.phase})"
    
    __str__ = __repr__