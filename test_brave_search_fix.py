#!/usr/bin/env python3
"""Quick test to verify the Brave Search API fix is working"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config import get_config
from backend.services.web_search_service import WebSearchService


async def test_brave_search_fix():
    """Test that the Brave Search API now returns results with the updated freshness filter"""
    print("🔍 Testing Brave Search API fix...")
    
    config = get_config()
    web_search_config = config.web_search
    
    # Check if API key is available
    if not web_search_config.api_key:
        print("⚠️  No BRAVE_SEARCH_API_KEY found in environment")
        return False
    
    try:
        # Initialize WebSearchService
        web_search_service = WebSearchService(
            api_key=web_search_config.api_key,
            cache_ttl=web_search_config.cache_ttl,
            max_cache_size=web_search_config.max_cache_size,
            timeout=web_search_config.timeout,
            educational_only=web_search_config.educational_only,
            min_relevance_score=web_search_config.min_relevance_score
        )
        print("✅ WebSearchService initialized")
        
        # Test multiple queries to verify the fix works consistently
        test_queries = [
            "elementary music rhythm activities",
            "music lesson plans for kindergarten",
            "teaching music theory to children"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            
            search_context = await web_search_service.search_educational_resources(
                query=query,
                max_results=5,
                grade_level="elementary",
                subject="music"
            )
            
            if search_context and search_context.results:
                print(f"✅ SUCCESS: Found {len(search_context.results)} results")
                for j, result in enumerate(search_context.results[:3], 1):
                    print(f"  {j}. {result.title}")
                    print(f"     URL: {result.url}")
                    print(f"     Domain: {result.domain} | Relevance: {result.relevance_score:.2f}")
            else:
                print(f"❌ FAILED: No results found")
                return False
        
        print(f"\n🎉 All tests passed! The Brave Search API fix is working correctly.")
        print(f"   Freshness filter changed from 'pd' (past day) to 'pw' (past week)")
        return True
        
    except Exception as e:
        print(f"❌ Error testing web search: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_brave_search_fix())
    sys.exit(0 if success else 1)