"""Node component for PocketFlow framework"""

from typing import Any, Dict, Optional


class Node:
    """Basic unit of computation in the graph"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.metadata: Dict[str, Any] = {}
    
    def process(self, input_data: Any) -> Any:
        """Process input data and return output"""
        raise NotImplementedError("Subclasses must implement process method")
    
    def __repr__(self) -> str:
        return f"Node(name={self.name})"