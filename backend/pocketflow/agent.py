"""Agent component for PocketFlow framework"""

from typing import Any, Dict, List, Optional, Callable
from .flow import Flow
from .store import Store


class Agent:
    """Base class for conversational agents"""
    
    def __init__(self, flow: Flow, store: Store, name: Optional[str] = None):
        self.flow = flow
        self.store = store
        self.name = name or self.__class__.__name__
        self.conversation_history: List[Dict[str, Any]] = []
        self.state_handlers: Dict[str, Callable[[str], str]] = {}
        self.current_state: str = "initial"
    
    def add_state_handler(self, state: str, handler: Callable[[str], str]) -> None:
        """Add a handler for a specific conversation state"""
        self.state_handlers[state] = handler
    
    def set_state(self, state: str) -> None:
        """Change the current conversation state"""
        self.store.set("current_state", state)
        self.current_state = state
    
    def get_state(self) -> str:
        """Get the current conversation state"""
        return self.current_state
    
    def chat(self, message: str) -> str:
        """Process a chat message and return response"""
        # Store message in history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "state": self.current_state,
            "timestamp": self._get_timestamp()
        })
        
        # Process message based on current state
        if self.current_state in self.state_handlers:
            response = self.state_handlers[self.current_state](message)
        else:
            response = self.handle_default(message)
        
        # Store response in history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "state": self.current_state,
            "timestamp": self._get_timestamp()
        })
        
        return response
    
    def handle_default(self, message: str) -> str:
        """Default message handler when no specific state handler exists"""
        return f"I received your message: {message}"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history"""
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __repr__(self) -> str:
        return f"Agent(name={self.name}, state={self.current_state})"