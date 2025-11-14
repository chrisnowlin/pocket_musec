#!/usr/bin/env python3
"""Direct test of web search service"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.services.web_search_service import WebSearchService
from backend.config import config


async def test_web_search():
    """Test web search service directly"""
    print("🔍 Testing Web Search Service Directly\n")

    # Check configuration
    search_config = config.web_search
    print(f"API Key configured: {bool(search_config.api_key)}")
    print(
        f"API Key (first 10 chars): {search_config.api_key[:10] if search_config.api_key else 'None'}..."
    )
    print(f"Educational only: {search_config.educational_only}")
    print(f"Min relevance score: {search_config.min_relevance_score}")

    if not search_config.api_key:
        print("❌ No API key configured - web search will not work")
        return False

    try:
        # Initialize web search service
        service = WebSearchService(
            api_key=search_config.api_key,
            cache_ttl=search_config.cache_ttl,
            max_cache_size=search_config.max_cache_size,
            timeout=search_config.timeout,
            educational_only=search_config.educational_only,
            min_relevance_score=search_config.min_relevance_score,
        )

        print("\n✅ WebSearchService initialized successfully")

        # Test search with simpler query first
        print("\n🔍 Testing search for 'music education'...")
        search_context = await service.search_educational_resources(
            query="music education", max_results=3, grade_level=None, subject="music"
        )

        if not search_context:
            print("❌ No search results returned")
            return False

        print(f"✅ Search completed in {search_context.search_time:.2f}s")
        print(f"Found {len(search_context.results)} results")

        # Test bibliography generation
        bibliography = search_context.get_citation_bibliography()
        print(f"\n📚 Generated bibliography ({len(bibliography)} chars):")
        print(bibliography[:500] + "..." if len(bibliography) > 500 else bibliography)

        return True

    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Direct Test: Web Search Service\n")

    success = asyncio.run(test_web_search())

    if success:
        print("\n🎉 Web search service test passed!")
    else:
        print("\n💥 Web search service test failed!")
        exit(1)
