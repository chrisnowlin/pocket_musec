"""Flow component for PocketFlow framework"""

from typing import Any, List, Dict, Optional
from .node import Node


class Flow:
    """Orchestrates node execution"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or "Flow"
        self.nodes: List[Node] = []
        self.execution_history: List[Dict[str, Any]] = []
    
    def add_node(self, node: Node) -> None:
        """Add a node to the flow"""
        self.nodes.append(node)
    
    def execute(self, initial_input: Any) -> Any:
        """Execute the flow with initial input"""
        self.execution_history.clear()
        current_data = initial_input
        
        for i, node in enumerate(self.nodes):
            try:
                result = node.process(current_data)
                self.execution_history.append({
                    "node": node.name,
                    "step": i,
                    "input": current_data,
                    "output": result,
                    "success": True
                })
                current_data = result
            except Exception as e:
                self.execution_history.append({
                    "node": node.name,
                    "step": i,
                    "input": current_data,
                    "output": None,
                    "success": False,
                    "error": str(e)
                })
                raise
        
        return current_data
    
    def get_execution_summary(self) -> List[Dict[str, Any]]:
        """Get summary of the last execution"""
        return self.execution_history.copy()
    
    def __len__(self) -> int:
        return len(self.nodes)
    
    def __repr__(self) -> str:
        return f"Flow(name={self.name}, nodes={len(self.nodes)})"