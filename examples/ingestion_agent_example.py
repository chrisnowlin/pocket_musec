"""Example usage of the IngestionAgent"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.pocketflow.ingestion_agent import IngestionAgent
from backend.pocketflow.ingestion_nodes import (
    FileValidationNode,
    DocumentClassificationNode,
    StandardsIngestionNode,
    IngestionRouterNode,
    IngestionSummaryNode,
)


def create_ingestion_flow():
    """Create a complete ingestion workflow"""
    flow = Flow("Document Ingestion Flow")

    # Add nodes to the flow
    flow.add_node(FileValidationNode())
    flow.add_node(DocumentClassificationNode())
    flow.add_node(IngestionRouterNode())
    flow.add_node(StandardsIngestionNode())
    flow.add_node(IngestionSummaryNode())

    return flow


def main():
    """Example of using the IngestionAgent"""
    # Create flow and store
    flow = create_ingestion_flow()
    store = Store()

    # Create ingestion agent
    agent = IngestionAgent(flow, store)

    print("🚀 PocketMusec IngestionAgent Example")
    print("=" * 50)

    # Simulate conversation
    conversation = [
        "",  # Initial message to trigger welcome
        "NC Music Standards.pdf",  # File path
        "yes",  # Confirm ingestion
        "quit",  # Exit
    ]

    for i, message in enumerate(conversation):
        print(f"\n--- Step {i + 1} ---")
        user_msg = message if message else "(starting)"
        print(f"User: {user_msg}")

        response = agent.chat(message)
        print(f"Agent: {response}")

        # Show current state
        print(f"State: {agent.get_state()}")

    # Show ingestion results
    results = agent.get_ingestion_results()
    if results:
        print(f"\n📊 Ingestion Results:")
        print(f"Standards: {results.get('standards_count', 0)}")
        print(f"Objectives: {results.get('objectives_count', 0)}")

    # Show conversation history
    history = agent.get_conversation_history()
    print(f"\n📝 Conversation History: {len(history)} messages")


def workflow_example():
    """Example of using the ingestion workflow directly"""
    print("\n🔧 PocketFlow Workflow Example")
    print("=" * 50)

    # Create flow
    flow = create_ingestion_flow()

    # Execute with sample data
    input_data = {"file_path": "NC Music Standards.pdf"}

    try:
        result = flow.execute(input_data)

        print("✅ Workflow completed successfully!")
        print(f"Final result: {result}")

        # Show execution summary
        summary = flow.get_execution_summary()
        print(f"\n📊 Execution Summary:")
        for step in summary:
            status = "✅" if step["success"] else "❌"
            print(f"{status} Step {step['step']}: {step['node']}")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")

        # Show execution summary up to failure
        summary = flow.get_execution_summary()
        print(f"\n📊 Execution Summary (up to failure):")
        for step in summary:
            status = "✅" if step["success"] else "❌"
            print(f"{status} Step {step['step']}: {step['node']}")
            if not step["success"]:
                print(f"   Error: {step.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
    workflow_example()
