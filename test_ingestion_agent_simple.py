"""Simple test for IngestionAgent"""

from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.pocketflow.ingestion_agent import IngestionAgent


def test_ingestion_agent_welcome():
    """Test the ingestion agent welcome flow"""
    # Create flow and store
    flow = Flow("Test Ingestion Flow")
    store = Store()

    # Create ingestion agent
    agent = IngestionAgent(flow, store)

    print("🧪 Testing IngestionAgent")
    print("=" * 50)

    # Test welcome message
    response = agent.chat("")
    print(f"\n1. Welcome State:")
    print(f"   State: {agent.get_state()}")
    print(f"   Response preview: {response[:100]}...")

    assert agent.get_state() == "file_path", (
        f"Expected 'file_path' state, got '{agent.get_state()}'"
    )
    assert "PDF document" in response, "Welcome message should mention PDF documents"

    # Test quit command
    response = agent.chat("quit")
    print(f"\n2. Quit State:")
    print(f"   State: {agent.get_state()}")
    print(f"   Response: {response}")

    assert agent.get_state() == "complete", (
        f"Expected 'complete' state, got '{agent.get_state()}'"
    )
    assert "cancelled" in response.lower() or "goodbye" in response.lower()

    print("\n✅ All tests passed!")


def test_ingestion_agent_invalid_file():
    """Test the ingestion agent with invalid file"""
    # Create flow and store
    flow = Flow("Test Ingestion Flow")
    store = Store()

    # Create ingestion agent
    agent = IngestionAgent(flow, store)

    print("\n🧪 Testing Invalid File Handling")
    print("=" * 50)

    # Trigger welcome
    agent.chat("")

    # Try invalid file
    response = agent.chat("nonexistent_file.pdf")
    print(f"\nInvalid file response preview: {response[:150]}...")

    assert "not found" in response.lower() or "invalid" in response.lower()
    assert agent.get_state() == "file_path", "Should stay in file_path state on error"

    print("\n✅ Invalid file handling test passed!")


def test_ingestion_context():
    """Test ingestion context storage"""
    # Create flow and store
    flow = Flow("Test Ingestion Flow")
    store = Store()

    # Create ingestion agent
    agent = IngestionAgent(flow, store)

    print("\n🧪 Testing Ingestion Context")
    print("=" * 50)

    # Check initial context is empty
    context = agent.get_ingestion_context()
    print(f"\nInitial context: {context}")
    assert len(context) == 0, "Initial context should be empty"

    # Trigger welcome and progress to file_path state
    agent.chat("")

    # Context should still be empty before file is provided
    context = agent.get_ingestion_context()
    print(f"Context after welcome: {context}")

    print("\n✅ Context test passed!")


if __name__ == "__main__":
    try:
        test_ingestion_agent_welcome()
        test_ingestion_agent_invalid_file()
        test_ingestion_context()
        print("\n" + "=" * 50)
        print("🎉 All IngestionAgent tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
