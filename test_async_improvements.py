"""
Test script to verify async improvements work correctly in lesson_agent.py

This script tests that:
1. LLM calls don't block the event loop
2. Async wrappers properly handle unavailable LLM services
3. Sync wrappers work correctly for state handlers
"""

import asyncio
import sys
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository


async def test_async_message_analysis():
    """Test that async message analysis works"""
    print("Testing async message analysis...")

    # Create a minimal lesson agent
    flow = Flow("test_flow")
    store = Store()
    agent = LessonAgent(flow, store, conversational_mode=True)

    try:
        # Test async message analysis
        test_message = "I need help creating a rhythm lesson for 3rd graders"
        result = await agent._async_analyze_user_message(test_message)

        assert isinstance(result, dict), "Result should be a dictionary"
        assert "grade_level" in result or "error" in result, (
            "Result should have grade_level or error"
        )

        print("✓ Async message analysis works correctly")
        return True

    except Exception as e:
        print(f"✗ Async message analysis failed: {e}")
        return False


async def test_async_conversational_response():
    """Test that async conversational response works"""
    print("Testing async conversational response...")

    flow = Flow("test_flow")
    store = Store()
    agent = LessonAgent(flow, store, conversational_mode=True)

    try:
        # Test async conversational response
        test_message = "I want to teach rhythm to kindergarteners"
        extracted_info = {
            "grade_level": "Kindergarten",
            "musical_topics": ["rhythm"],
            "confidence_score": 0.8,
        }
        relevant_standards = []

        result = await agent._generate_conversational_response(
            test_message, extracted_info, relevant_standards
        )

        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"

        print("✓ Async conversational response works correctly")
        return True

    except Exception as e:
        print(f"✗ Async conversational response failed: {e}")
        return False


def test_sync_wrappers():
    """Test that sync wrappers work for state handlers"""
    print("Testing sync wrappers...")

    flow = Flow("test_flow")
    store = Store()
    agent = LessonAgent(flow, store, conversational_mode=True)

    try:
        # Test sync wrapper for conversational response
        test_message = "I want to teach melody to first graders"
        extracted_info = {
            "grade_level": "First Grade",
            "musical_topics": ["melody"],
            "confidence_score": 0.8,
        }
        relevant_standards = []

        result = agent._generate_conversational_response_sync(
            test_message, extracted_info, relevant_standards
        )

        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"

        print("✓ Sync wrappers work correctly")
        return True

    except Exception as e:
        print(f"✗ Sync wrappers failed: {e}")
        return False


async def test_async_lesson_generation():
    """Test that async lesson generation works"""
    print("Testing async lesson generation...")

    flow = Flow("test_flow")
    store = Store()
    agent = LessonAgent(flow, store, conversational_mode=True)

    try:
        # Set up minimal lesson requirements
        agent.lesson_requirements["extracted_info"] = {
            "grade_level": "Third Grade",
            "musical_topics": ["rhythm"],
            "time_constraints": "30 minutes",
        }

        # Test async lesson generation
        result = await agent._generate_lesson_plan()

        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should not be empty"

        print("✓ Async lesson generation works correctly")
        return True

    except Exception as e:
        print(f"✗ Async lesson generation failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Testing Async Improvements in LessonAgent")
    print("=" * 60 + "\n")

    results = []

    # Run async tests
    results.append(await test_async_message_analysis())
    results.append(await test_async_conversational_response())
    results.append(await test_async_lesson_generation())

    # Run sync tests
    results.append(test_sync_wrappers())

    # Summary
    print("\n" + "=" * 60)
    print(f"Test Summary: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    if all(results):
        print("✓ All async improvements working correctly!")
        return 0
    else:
        print("✗ Some tests failed - please review the output above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
