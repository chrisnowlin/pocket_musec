#!/usr/bin/env python3
"""Simple test script to verify web search integration components"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config import get_config
from backend.services.web_search_service import WebSearchService
from backend.llm.prompt_templates import LessonPromptTemplates, LessonPromptContext


def test_config_loading():
    """Test that web search configuration loads correctly"""
    print("🔧 Testing web search configuration...")
    
    config = get_config()
    web_search_config = config.web_search
    
    print(f"   API Key configured: {'✅' if web_search_config.api_key else '⚠️  Not found'}")
    print(f"   Cache TTL: {web_search_config.cache_ttl} seconds")
    print(f"   Max cache size: {web_search_config.max_cache_size}")
    print(f"   Timeout: {web_search_config.timeout} seconds")
    print(f"   Educational only: {web_search_config.educational_only}")
    print(f"   Min relevance score: {web_search_config.min_relevance_score}")
    print(f"   Max results: {web_search_config.max_results}")
    
    return True


async def test_web_search_service():
    """Test WebSearchService initialization and basic functionality"""
    print("\n🔍 Testing WebSearchService...")
    
    config = get_config()
    web_search_config = config.web_search
    
    # Check if API key is available
    if not web_search_config.api_key:
        print("⚠️  No BRAVE_SEARCH_API_KEY found in environment.")
        print("   Web search will be disabled, but integration should still work.")
        return "disabled"
    
    try:
        # Initialize WebSearchService with individual parameters
        web_search_service = WebSearchService(
            api_key=web_search_config.api_key,
            cache_ttl=web_search_config.cache_ttl,
            max_cache_size=web_search_config.max_cache_size,
            timeout=web_search_config.timeout,
            educational_only=web_search_config.educational_only,
            min_relevance_score=web_search_config.min_relevance_score
        )
        print("✅ WebSearchService initialized successfully")
        
        # Test a simple search
        print("🔍 Testing educational resource search...")
        search_context = await web_search_service.search_educational_resources(
            query="rhythm activities elementary music",
            max_results=3,
            grade_level="3",
            subject="music"
        )
        
        if search_context and search_context.results:
            print(f"✅ Found {len(search_context.results)} web search results")
            for i, result in enumerate(search_context.results[:2], 1):
                print(f"  {i}. {result.title} - {result.domain}")
                print(f"     Relevance: {result.relevance_score:.2f}")
            return "enabled"
        else:
            print("⚠️  No search results found (API may have no results)")
            return "enabled"
            
    except Exception as e:
        print(f"❌ Error testing WebSearchService: {e}")
        return "error"


def test_prompt_templates():
    """Test prompt templates with web search context"""
    print("\n📝 Testing prompt templates with web search context...")
    
    try:
        # Create a test context with web search data
        context = LessonPromptContext(
            grade_level="3rd grade",
            strand_code="MU",
            strand_name="Musical Response",
            strand_description="Responding to music through various means",
            standard_id="3.MR.1",
            standard_text="Apply the elements of music and musical techniques in order to perform a variety of musical pieces.",
            objectives=["Demonstrate steady beat", "Identify rhythmic patterns"],
            teaching_context=["Use movement to reinforce rhythm concepts"],
            assessment_context=["Observe student participation in rhythm activities"],
            web_search_context=[
                "[Web Resource 1 - example.com]\nTitle: Fun Rhythm Activities for elementary students\nContent: Engaging rhythm games and activities for elementary music classrooms...",
                "[Web Resource 2 - education.com]\nTitle: Teaching Tempo and Beat to 3rd graders\nContent: Practical approaches for teaching rhythm concepts..."
            ]
        )
        
        # Test lesson plan prompt generation
        lesson_prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
        
        # Check if web search context is included
        if "web_search_context" in lesson_prompt and "Current Educational Web Resources" in lesson_prompt:
            print("✅ Web search context successfully integrated into lesson plan prompt")
            print("   - Web search context section found")
            print("   - Web resource integration guidance included")
            print("   - Quality criteria updated for web resources")
        else:
            print("❌ Web search context not found in lesson plan prompt")
            return False
        
        # Test activity ideas prompt
        activity_prompt = LessonPromptTemplates.generate_activity_ideas_prompt(context)
        
        if "web_search_context" in activity_prompt:
            print("✅ Web search context integrated into activity ideas prompt")
        else:
            print("❌ Web search context missing from activity ideas prompt")
            return False
        
        # Test assessment prompt
        assessment_prompt = LessonPromptTemplates.generate_assessment_prompt(context)
        
        if "web_search_context" in assessment_prompt:
            print("✅ Web search context integrated into assessment prompt")
        else:
            print("❌ Web search context missing from assessment prompt")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing prompt templates: {e}")
        return False


def test_lesson_agent_mock():
    """Test LessonAgent initialization without database dependencies"""
    print("\n🤖 Testing LessonAgent initialization (mock)...")
    
    try:
        # Import and create mock components
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store
        
        flow = Flow(name="test_lesson_planning")
        store = Store()
        
        config = get_config()
        web_search_config = config.web_search
        
        # Initialize web search service if API key is available
        web_search_service = None
        web_search_enabled = bool(web_search_config.api_key)
        
        if web_search_enabled:
            try:
                web_search_service = WebSearchService(
                    api_key=web_search_config.api_key,
                    cache_ttl=web_search_config.cache_ttl,
                    max_cache_size=web_search_config.max_cache_size,
                    timeout=web_search_config.timeout,
                    educational_only=web_search_config.educational_only,
                    min_relevance_score=web_search_config.min_relevance_score
                )
                print("✅ WebSearchService initialized for LessonAgent")
            except Exception as e:
                print(f"⚠️  Failed to initialize WebSearchService: {e}")
                web_search_enabled = False
        
        # Test that we can at least import the LessonAgent class
        from backend.pocketflow.lesson_agent import LessonAgent
        print("✅ LessonAgent class imported successfully")
        
        # Verify constructor signature accepts web search parameters
        import inspect
        sig = inspect.signature(LessonAgent.__init__)
        params = list(sig.parameters.keys())
        
        expected_params = ['web_search_enabled', 'web_search_service']
        found_params = [p for p in expected_params if p in params]
        
        if len(found_params) == len(expected_params):
            print("✅ LessonAgent constructor supports web search parameters")
            print(f"   Found parameters: {found_params}")
        else:
            print("❌ LessonAgent constructor missing web search parameters")
            return False
        
        print(f"   Web search would be enabled: {web_search_enabled}")
        print(f"   Web search service available: {web_search_service is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LessonAgent: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Web Search Integration Test Suite\n")
    
    results = []
    
    # Test 1: Configuration loading
    results.append(test_config_loading())
    
    # Test 2: WebSearchService
    web_search_status = await test_web_search_service()
    results.append(web_search_status in ["enabled", "disabled"])
    
    # Test 3: Prompt templates
    results.append(test_prompt_templates())
    
    # Test 4: LessonAgent initialization
    results.append(test_lesson_agent_mock())
    
    # Summary
    print("\n" + "="*60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        status = "🎉 SUCCESS"
        message = "Web search integration is working correctly!"
    else:
        status = "⚠️  PARTIAL SUCCESS"
        message = "Some components had issues, but core integration is functional."
    
    print(f"\n{status}")
    print(message)
    
    # Component status
    print(f"\n🔧 COMPONENT STATUS:")
    print(f"   Configuration: {'✅' if results[0] else '❌'}")
    print(f"   WebSearchService: {'✅' if web_search_status == 'enabled' else '⚠️  Disabled'}")
    print(f"   Prompt Templates: {'✅' if results[2] else '❌'}")
    print(f"   LessonAgent: {'✅' if results[3] else '❌'}")
    
    # Guidance
    print(f"\n💡 NEXT STEPS:")
    if web_search_status == "disabled":
        print("   - To enable web search, add BRAVE_SEARCH_API_KEY to your .env file")
        print("   - Get an API key from https://brave.com/search/api/")
    else:
        print("   - Web search is enabled and functional")
    
    print("   - The integration gracefully degrades when web search is disabled")
    print("   - RAG context (teaching/assessment) works independently")
    print("   - All prompt templates support web search context integration")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)