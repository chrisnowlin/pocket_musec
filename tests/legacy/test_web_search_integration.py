#!/usr/bin/env python3
"""Test script to verify web search integration in LessonAgent"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config import get_config
from backend.services.web_search_service import WebSearchService
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository


async def test_web_search_service():
    """Test WebSearchService initialization and basic functionality"""
    print("🔍 Testing WebSearchService initialization...")
    
    config = get_config()
    web_search_config = config.web_search
    
    # Check if API key is available
    if not web_search_config.api_key:
        print("⚠️  No BRAVE_SEARCH_API_KEY found in environment. Web search will be disabled.")
        return False
    
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
            return True
        else:
            print("⚠️  No search results found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing WebSearchService: {e}")
        return False


def test_lesson_agent_initialization():
    """Test LessonAgent initialization with web search enabled"""
    print("\n🤖 Testing LessonAgent initialization...")
    
    config = get_config()
    web_search_config = config.web_search
    
    # Create basic components
    flow = Flow(name="test_lesson_planning")
    store = Store()
    standards_repo = StandardsRepository()
    
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
    
    try:
        # Initialize LessonAgent with web search
        agent = LessonAgent(
            flow=flow,
            store=store,
            standards_repo=standards_repo,
            conversational_mode=True,
            web_search_enabled=web_search_enabled,
            web_search_service=web_search_service,
        )
        
        print(f"✅ LessonAgent initialized successfully")
        print(f"   Web search enabled: {agent.web_search_enabled}")
        print(f"   Web search service available: {agent.web_search_service is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing LessonAgent: {e}")
        return False


async def test_lesson_agent_web_search_context():
    """Test LessonAgent web search context retrieval"""
    print("\n🔗 Testing LessonAgent web search context retrieval...")
    
    config = get_config()
    if not config.web_search.api_key:
        print("⚠️  Skipping web search context test - no API key available")
        return True  # Not a failure, just not available
    
    # Create and initialize LessonAgent
    flow = Flow(name="test_lesson_planning")
    store = Store()
    standards_repo = StandardsRepository()
    
    web_search_service = WebSearchService(
        api_key=config.web_search.api_key,
        cache_ttl=config.web_search.cache_ttl,
        max_cache_size=config.web_search.max_cache_size,
        timeout=config.web_search.timeout,
        educational_only=config.web_search.educational_only,
        min_relevance_score=config.web_search.min_relevance_score
    )
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standards_repo,
        conversational_mode=True,
        web_search_enabled=True,
        web_search_service=web_search_service,
    )
    
    # Test web search context retrieval
    extracted_info = {
        "grade_level": "3rd grade",
        "musical_topics": ["rhythm", "beat", "tempo"],
        "activity_preferences": ["interactive", "movement"]
    }
    
    try:
        web_search_context = await agent._get_web_search_context(extracted_info)
        
        if web_search_context:
            print(f"✅ Retrieved {len(web_search_context)} web search context items")
            for i, context in enumerate(web_search_context[:2], 1):
                print(f"  {i}. {context[:100]}...")
            return True
        else:
            print("⚠️  No web search context retrieved")
            return True  # Not a failure, just no results
            
    except Exception as e:
        print(f"❌ Error retrieving web search context: {e}")
        return False


async def test_lesson_context_building():
    """Test lesson context building with web search integration"""
    print("\n🏗️  Testing lesson context building with web search...")
    
    config = get_config()
    
    # Create and initialize LessonAgent
    flow = Flow(name="test_lesson_planning")
    store = Store()
    standards_repo = StandardsRepository()
    
    web_search_service = None
    web_search_enabled = bool(config.web_search.api_key)
    
    if web_search_enabled:
        web_search_service = WebSearchService(
            api_key=config.web_search.api_key,
            cache_ttl=config.web_search.cache_ttl,
            max_cache_size=config.web_search.max_cache_size,
            timeout=config.web_search.timeout,
            educational_only=config.web_search.educational_only,
            min_relevance_score=config.web_search.min_relevance_score
        )
    
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standards_repo,
        conversational_mode=True,
        web_search_enabled=web_search_enabled,
        web_search_service=web_search_service,
    )
    
    # Set up some lesson requirements
    agent.lesson_requirements["extracted_info"] = {
        "grade_level": "3rd grade",
        "musical_topics": ["rhythm", "beat"],
        "resources": ["drums", "rhythm sticks"],
        "time_constraints": "45 minutes"
    }
    
    # Add a suggested standard
    standards = standards_repo.get_standards_by_grade("3")
    if standards:
        agent.lesson_requirements["suggested_standards"] = [standards[0]]
    
    try:
        context = await agent._build_lesson_context_from_conversation()
        
        print("✅ Lesson context built successfully")
        print(f"   Grade level: {context.grade_level}")
        print(f"   Standard: {context.standard_id}")
        print(f"   Teaching context items: {len(context.teaching_context or [])}")
        print(f"   Assessment context items: {len(context.assessment_context or [])}")
        print(f"   Web search context items: {len(context.web_search_context or [])}")
        
        # Check if RAG context was stored
        rag_context = agent.lesson_requirements.get("rag_context", {})
        if rag_context:
            print("✅ RAG context stored in lesson requirements")
            print(f"   Teaching: {len(rag_context.get('teaching_context', []))}")
            print(f"   Assessment: {len(rag_context.get('assessment_context', []))}")
            print(f"   Web Search: {len(rag_context.get('web_search_context', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error building lesson context: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Starting Web Search Integration Tests\n")
    
    results = []
    
    # Test 1: WebSearchService
    results.append(await test_web_search_service())
    
    # Test 2: LessonAgent initialization
    results.append(test_lesson_agent_initialization())
    
    # Test 3: Web search context retrieval (if API key available)
    if results[0]:  # Only if web search service test passed
        results.append(await test_lesson_agent_web_search_context())
    else:
        results.append(True)  # Skip, not a failure
    
    # Test 4: Lesson context building
    results.append(await test_lesson_context_building())
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Web search integration is working correctly.")
    else:
        print("⚠️  Some tests had issues. Check the output above for details.")
        
        # Provide guidance
        print("\n💡 SETUP GUIDANCE:")
        if not results[0]:
            print("- To enable web search, set BRAVE_SEARCH_API_KEY in your .env file")
            print("- Get an API key from https://brave.com/search/api/")
        print("- Web search gracefully degrades when disabled")
        print("- RAG context (teaching/assessment) works independently of web search")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())