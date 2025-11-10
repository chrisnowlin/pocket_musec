"""Tests for PocketFlow Agent component"""

def test_agent_creation():
    """Test that an Agent can be created"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    assert agent is not None
    assert agent.flow == flow
    assert agent.store == store
    assert agent.name == "Agent"
    assert agent.current_state == "initial"


def test_agent_with_name():
    """Test Agent creation with custom name"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store, "TestAgent")
    
    assert agent.name == "TestAgent"


def test_agent_state_management():
    """Test agent state management"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    agent.set_state("new_state")
    assert agent.get_state() == "new_state"
    assert agent.current_state == "new_state"
    assert store.get("current_state") == "new_state"


def test_agent_state_handlers():
    """Test adding and using state handlers"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    # Add a state handler
    def greeting_handler(message):
        return f"Hello! You said: {message}"
    
    agent.add_state_handler("greeting", greeting_handler)
    agent.set_state("greeting")
    
    response = agent.chat("world")
    assert response == "Hello! You said: world"


def test_agent_conversation_history():
    """Test that conversation history is tracked"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    agent.chat("message 1")
    agent.chat("message 2")
    
    history = agent.get_conversation_history()
    assert len(history) == 4  # 2 user messages + 2 responses
    
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "message 1"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[2]["content"] == "message 2"
    assert history[3]["role"] == "assistant"


def test_agent_clear_history():
    """Test clearing conversation history"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    agent.chat("message")
    assert len(agent.get_conversation_history()) > 0
    
    agent.clear_history()
    assert len(agent.get_conversation_history()) == 0


def test_agent_default_handler():
    """Test default message handler when no state handler exists"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store)
    
    response = agent.chat("test message")
    assert "test message" in response


def test_agent_repr():
    """Test Agent string representation"""
    from backend.pocketflow.agent import Agent
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.store import Store
    
    flow = Flow()
    store = Store()
    agent = Agent(flow, store, "TestAgent")
    
    assert repr(agent) == "Agent(name=TestAgent, state=initial)"
    
    agent.set_state("new_state")
    assert repr(agent) == "Agent(name=TestAgent, state=new_state)"