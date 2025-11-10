"""Tests for PocketFlow Node component"""

def test_node_creation():
    """Test that a Node can be created"""
    from backend.pocketflow.node import Node
    
    class TestNode(Node):
        def process(self, input_data):
            return input_data
    
    node = TestNode()
    assert node is not None