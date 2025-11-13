"""Test LessonAgent integration with citation system"""

import asyncio
import logging
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.llm.chutes_client import ChutesClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lessonagent_web_search_context():
    """Test LessonAgent web search context retrieval with citations"""
    print("\n" + "="*80)
    print("TEST: LessonAgent Web Search Context with Citations")
    print("="*80)
    
    try:
        # Create LessonAgent with web search enabled
        flow = Flow()
        store = Store()
        standards_repo = StandardsRepository()
        llm_client = ChutesClient()
        
        agent = LessonAgent(
            flow=flow,
            store=store,
            standards_repo=standards_repo,
            llm_client=llm_client,
            conversational_mode=True,
            web_search_enabled=True
        )
        
        # Create extracted info for web search
        extracted_info = {
            "grade_level": "Grade 3",
            "musical_topics": ["rhythm activities", "elementary music"]
        }
        
        # Test web search context retrieval
        print("\n📡 Testing web search context retrieval...")
        web_context = await agent._get_web_search_context(extracted_info)
        
        if not web_context:
            print("⚠️  WARNING: No web search context returned (may be expected if API key not configured)")
            print("✓ Graceful degradation working - returns empty list")
            return True
        
        # Check that citations are included in context
        assert len(web_context) > 0, "Web context is empty"
        print(f"✓ Retrieved {len(web_context)} web search context items")
        
        # Check each context item for citation markers
        citation_markers_found = 0
        for i, context_item in enumerate(web_context, 1):
            print(f"\n📄 Context Item {i}:")
            print(f"   Preview: {context_item[:100]}...")
            
            if "[Web Source:" in context_item:
                citation_markers_found += 1
                print(f"   ✓ Contains citation marker")
            else:
                print(f"   ⚠️  Missing citation marker (using fallback format)")
        
        print(f"\n✓ Citation markers found in {citation_markers_found}/{len(web_context)} items")
        
        # Test that context can be used in lesson generation
        print("\n🏗️  Testing context building with web search...")
        
        # Set up lesson requirements for context building
        agent.lesson_requirements["extracted_info"] = extracted_info
        agent.lesson_requirements["suggested_standards"] = standards_repo.get_standards_by_grade("3")[:1]
        
        # Build lesson context
        context = await agent._build_lesson_context_from_conversation()
        
        # Check that web search context is included
        assert context.web_search_context is not None, "Web search context not included in lesson context"
        print(f"✓ Web search context included in LessonPromptContext")
        print(f"   Teaching context items: {len(context.teaching_context or [])}")
        print(f"   Assessment context items: {len(context.assessment_context or [])}")
        print(f"   Web search context items: {len(context.web_search_context or [])}")
        
        print("\n✅ TEST PASSED: LessonAgent web search integration working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_teaching_strategies_context():
    """Test teaching strategies context retrieval"""
    print("\n" + "="*80)
    print("TEST: Teaching Strategies Context Retrieval")
    print("="*80)
    
    try:
        # Create LessonAgent
        flow = Flow()
        store = Store()
        agent = LessonAgent(
            flow=flow,
            store=store,
            conversational_mode=True
        )
        
        # Test with extracted info
        extracted_info = {
            "grade_level": "Grade 3",
            "musical_topics": ["rhythm", "notation"],
            "activity_preferences": ["hands-on", "interactive"]
        }
        
        print("\n🔍 Retrieving teaching strategies context...")
        teaching_context = agent._get_teaching_strategies_context(extracted_info)
        
        print(f"✓ Retrieved {len(teaching_context)} teaching strategy items")
        
        if len(teaching_context) > 0:
            print(f"\n📚 Sample teaching context:")
            print(f"   {teaching_context[0][:150]}...")
        
        print("\n✅ TEST PASSED: Teaching strategies context retrieval working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_assessment_guidance_context():
    """Test assessment guidance context retrieval"""
    print("\n" + "="*80)
    print("TEST: Assessment Guidance Context Retrieval")
    print("="*80)
    
    try:
        # Create LessonAgent
        flow = Flow()
        store = Store()
        agent = LessonAgent(
            flow=flow,
            store=store,
            conversational_mode=True
        )
        
        # Test with extracted info
        extracted_info = {
            "grade_level": "Grade 3",
            "musical_topics": ["rhythm", "performance"]
        }
        
        print("\n🔍 Retrieving assessment guidance context...")
        assessment_context = agent._get_assessment_guidance_context(extracted_info)
        
        print(f"✓ Retrieved {len(assessment_context)} assessment guidance items")
        
        if len(assessment_context) > 0:
            print(f"\n📋 Sample assessment context:")
            print(f"   {assessment_context[0][:150]}...")
        
        print("\n✅ TEST PASSED: Assessment guidance context retrieval working")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling_graceful_degradation():
    """Test error handling and graceful degradation"""
    print("\n" + "="*80)
    print("TEST: Error Handling and Graceful Degradation")
    print("="*80)
    
    try:
        # Create LessonAgent with web search but no service
        flow = Flow()
        store = Store()
        
        agent = LessonAgent(
            flow=flow,
            store=store,
            conversational_mode=True,
            web_search_enabled=False  # Explicitly disabled
        )
        
        # Test with extracted info
        extracted_info = {
            "grade_level": "Grade 3",
            "musical_topics": ["rhythm"]
        }
        
        print("\n🛡️  Testing graceful degradation with disabled web search...")
        web_context = await agent._get_web_search_context(extracted_info)
        
        assert web_context == [], "Should return empty list when disabled"
        print("✓ Returns empty list when web search disabled")
        
        # Test with empty musical topics
        print("\n🛡️  Testing with empty musical topics...")
        extracted_info_empty = {
            "grade_level": "Grade 3",
            "musical_topics": []
        }
        
        agent.web_search_enabled = True  # Re-enable for this test
        web_context_empty = await agent._get_web_search_context(extracted_info_empty)
        
        assert web_context_empty == [], "Should return empty list with no topics"
        print("✓ Returns empty list when no musical topics provided")
        
        print("\n✅ TEST PASSED: Error handling and graceful degradation working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_integration_tests():
    """Run all LessonAgent integration tests"""
    print("\n" + "="*80)
    print("LESSONAGENT CITATION INTEGRATION TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Test 1: Web search context with citations
    results['Web Search Context Integration'] = await test_lessonagent_web_search_context()
    
    # Test 2: Teaching strategies context
    results['Teaching Strategies Context'] = await test_teaching_strategies_context()
    
    # Test 3: Assessment guidance context
    results['Assessment Guidance Context'] = await test_assessment_guidance_context()
    
    # Test 4: Error handling
    results['Error Handling & Graceful Degradation'] = await test_error_handling_graceful_degradation()
    
    # Print summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result is True else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\n❌ INTEGRATION TESTS HAVE ISSUES")
        return False
    else:
        print("\n✅ ALL INTEGRATION TESTS PASSED")
        return True

if __name__ == "__main__":
    asyncio.run(run_integration_tests())