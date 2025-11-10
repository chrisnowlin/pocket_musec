"""Tests for PocketFlow Flow component"""

def test_flow_creation():
    """Test that a Flow can be created"""
    from backend.pocketflow.flow import Flow
    
    flow = Flow()
    assert flow is not None
    assert len(flow) == 0
    assert flow.name == "Flow"


def test_flow_with_name():
    """Test Flow creation with custom name"""
    from backend.pocketflow.flow import Flow
    
    flow = Flow("TestFlow")
    assert flow.name == "TestFlow"


def test_flow_add_node():
    """Test adding nodes to a flow"""
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.node import Node
    
    class TestNode(Node):
        def process(self, input_data):
            return input_data
    
    flow = Flow()
    node = TestNode("test_node")
    flow.add_node(node)
    
    assert len(flow) == 1


def test_flow_execute():
    """Test executing a flow with nodes"""
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.node import Node
    
    class AddNode(Node):
        def process(self, input_data):
            return input_data + 1
    
    class MultiplyNode(Node):
        def process(self, input_data):
            return input_data * 2
    
    flow = Flow("test_flow")
    flow.add_node(AddNode("add"))
    flow.add_node(MultiplyNode("multiply"))
    
    result = flow.execute(5)
    assert result == 12  # (5 + 1) * 2


def test_flow_execution_history():
    """Test that execution history is tracked"""
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.node import Node
    
    class TestNode(Node):
        def process(self, input_data):
            return f"processed_{input_data}"
    
    flow = Flow()
    flow.add_node(TestNode("node1"))
    flow.add_node(TestNode("node2"))
    
    result = flow.execute("input")
    history = flow.get_execution_summary()
    
    assert len(history) == 2
    assert history[0]["node"] == "node1"
    assert history[1]["node"] == "node2"
    assert all(h["success"] for h in history)


def test_flow_execution_error():
    """Test that execution errors are tracked"""
    from backend.pocketflow.flow import Flow
    from backend.pocketflow.node import Node
    
    class ErrorNode(Node):
        def process(self, input_data):
            raise ValueError("Test error")
    
    class TestNode(Node):
        def process(self, input_data):
            return input_data
    
    flow = Flow()
    flow.add_node(TestNode("good_node"))
    flow.add_node(ErrorNode("bad_node"))
    
    try:
        flow.execute("input")
        assert False, "Should have raised an error"
    except ValueError:
        pass
    
    history = flow.get_execution_summary()
    assert len(history) == 2
    assert history[0]["success"] is True
    assert history[1]["success"] is False
    assert "Test error" in history[1]["error"]


def test_flow_repr():
    """Test Flow string representation"""
    from backend.pocketflow.flow import Flow
    
    flow = Flow("test")
    assert repr(flow) == "Flow(name=test, nodes=0)"
    
    # Add a node
    from backend.pocketflow.node import Node
    
    class TestNode(Node):
        def process(self, input_data):
            return input_data
    
    flow.add_node(TestNode())
    assert repr(flow) == "Flow(name=test, nodes=1)"