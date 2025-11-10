"""Message passing utilities for PocketFlow framework"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Represents a message passed between nodes"""
    sender: str
    receiver: str
    content: Any
    message_type: str = "data"
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


class MessageBus:
    """Handles message passing between nodes"""
    
    def __init__(self):
        self.messages: List[Message] = []
        self.subscribers: Dict[str, List[str]] = {}
    
    def send(self, sender: str, receiver: str, content: Any, 
             message_type: str = "data", metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Send a message from sender to receiver"""
        message = Message(
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.messages.append(message)
        return message
    
    def subscribe(self, node: str, to_sender: str) -> None:
        """Subscribe a node to messages from another node"""
        if to_sender not in self.subscribers:
            self.subscribers[to_sender] = []
        if node not in self.subscribers[to_sender]:
            self.subscribers[to_sender].append(node)
    
    def get_messages_for(self, receiver: str, since: Optional[str] = None) -> List[Message]:
        """Get messages for a specific receiver, optionally since a timestamp"""
        messages = [msg for msg in self.messages if msg.receiver == receiver]
        if since:
            messages = [msg for msg in messages if msg.timestamp and msg.timestamp >= since]
        return messages
    
    def get_messages_from(self, sender: str, since: Optional[str] = None) -> List[Message]:
        """Get messages from a specific sender, optionally since a timestamp"""
        messages = [msg for msg in self.messages if msg.sender == sender]
        if since:
            messages = [msg for msg in messages if msg.timestamp and msg.timestamp >= since]
        return messages
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)