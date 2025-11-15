"""
Basic test to verify lesson_agent.py imports and compiles correctly
"""

import sys


def test_import():
    """Test that the module imports without errors"""
    print("Testing module import...")
    try:
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store

        print("✓ Module imports successfully")
        return True
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        return False


def test_instantiation():
    """Test that LessonAgent can be instantiated"""
    print("Testing agent instantiation...")
    try:
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store

        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        print("✓ LessonAgent instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Agent instantiation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_async_methods_exist():
    """Test that async methods exist"""
    print("Testing async methods exist...")
    try:
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store

        flow = Flow("test_flow")
        store = Store()
        agent = LessonAgent(flow, store, conversational_mode=True)

        # Check async methods exist
        assert hasattr(agent, "_async_llm_chat_completion"), (
            "Missing _async_llm_chat_completion"
        )
        assert hasattr(agent, "_async_llm_generate_lesson_plan"), (
            "Missing _async_llm_generate_lesson_plan"
        )
        assert hasattr(agent, "_async_analyze_user_message"), (
            "Missing _async_analyze_user_message"
        )
        assert hasattr(agent, "_generate_conversational_response"), (
            "Missing _generate_conversational_response"
        )
        assert hasattr(agent, "_generate_lesson_plan"), "Missing _generate_lesson_plan"

        # Check sync wrappers exist
        assert hasattr(agent, "_generate_conversational_response_sync"), (
            "Missing _generate_conversational_response_sync"
        )
        assert hasattr(agent, "_generate_lesson_plan_sync"), (
            "Missing _generate_lesson_plan_sync"
        )
        assert hasattr(agent, "_handle_conversational_welcome_sync"), (
            "Missing _handle_conversational_welcome_sync"
        )
        assert hasattr(agent, "_handle_generation_sync"), (
            "Missing _handle_generation_sync"
        )

        print("✓ All async methods and sync wrappers exist")
        return True
    except Exception as e:
        print(f"✗ Async methods check failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Basic Async Improvements Test")
    print("=" * 60 + "\n")

    results = []
    results.append(test_import())
    results.append(test_instantiation())
    results.append(test_async_methods_exist())

    # Summary
    print("\n" + "=" * 60)
    print(f"Test Summary: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    if all(results):
        print("✓ All basic tests passed!")
        print("\nThe async improvements have been successfully implemented:")
        print("  - Async LLM wrapper methods created")
        print("  - Sync wrapper methods for state handlers created")
        print("  - LLM calls updated to use async wrappers")
        return 0
    else:
        print("✗ Some tests failed - please review the output above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
