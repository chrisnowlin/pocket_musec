"""Tests for PocketFlow Message component"""

def test_message_creation():
    """Test that a Message can be created"""
    from backend.pocketflow.message import Message
    
    message = Message("sender", "receiver", "content")
    
    assert message.sender == "sender"
    assert message.receiver == "receiver"
    assert message.content == "content"
    assert message.message_type == "data"
    assert message.timestamp is not None
    assert message.metadata == {}


def test_message_with_options():
    """Test Message creation with custom options"""
    from backend.pocketflow.message import Message
    
    message = Message(
        sender="node1",
        receiver="node2", 
        content="test",
        message_type="command",
        metadata={"priority": "high"}
    )
    
    assert message.message_type == "command"
    assert message.metadata["priority"] == "high"


def test_message_bus_creation():
    """Test that a MessageBus can be created"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    assert bus is not None
    assert bus.get_message_count() == 0


def test_message_bus_send():
    """Test sending messages through the bus"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    message = bus.send("sender", "receiver", "content")
    
    assert bus.get_message_count() == 1
    assert message.sender == "sender"
    assert message.receiver == "receiver"


def test_message_bus_subscribe():
    """Test subscribing to messages"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    bus.subscribe("node1", "sender")
    
    assert "node1" in bus.subscribers["sender"]


def test_message_bus_get_messages_for():
    """Test getting messages for a specific receiver"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    bus.send("sender1", "receiver1", "content1")
    bus.send("sender2", "receiver1", "content2")
    bus.send("sender3", "receiver2", "content3")
    
    messages = bus.get_messages_for("receiver1")
    assert len(messages) == 2
    assert all(msg.receiver == "receiver1" for msg in messages)


def test_message_bus_get_messages_from():
    """Test getting messages from a specific sender"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    bus.send("sender1", "receiver1", "content1")
    bus.send("sender1", "receiver2", "content2")
    bus.send("sender2", "receiver1", "content3")
    
    messages = bus.get_messages_from("sender1")
    assert len(messages) == 2
    assert all(msg.sender == "sender1" for msg in messages)


def test_message_bus_clear():
    """Test clearing all messages"""
    from backend.pocketflow.message import MessageBus
    
    bus = MessageBus()
    bus.send("sender", "receiver", "content")
    
    assert bus.get_message_count() == 1
    
    bus.clear()
    assert bus.get_message_count() == 0