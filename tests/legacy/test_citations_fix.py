#!/usr/bin/env python3
"""Test script to verify citation system fixes"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.services.web_search_service import SearchResult, WebSearchContext


def test_search_result_citation():
    """Test SearchResult citation formatting"""
    print("Testing SearchResult citation formatting...")

    # Create a search result
    result = SearchResult(
        title="Teaching Rhythm in Elementary Music",
        url="https://www.musiceducators.org/teaching-rhythm",
        snippet="This article provides effective strategies for teaching rhythm concepts to elementary students through engaging activities and games.",
    )

    # Test citation format
    citation = result.to_citation_format(1)
    print(f"Citation: {citation}")

    # Test context with citation
    context = result.to_context_with_citation(1)
    print(f"Context:\n{context}")

    return True


def test_web_search_context_bibliography():
    """Test WebSearchContext bibliography generation"""
    print("\nTesting WebSearchContext bibliography generation...")

    # Create multiple search results
    results = [
        SearchResult(
            title="Teaching Rhythm in Elementary Music",
            url="https://www.musiceducators.org/teaching-rhythm",
            snippet="This article provides effective strategies for teaching rhythm concepts to elementary students through engaging activities and games.",
        ),
        SearchResult(
            title="Percussion Instruments for the Classroom",
            url="https://www.nafme.org/classroom-percussion",
            snippet="A guide to using percussion instruments in elementary music education to develop rhythmic skills.",
        ),
        SearchResult(
            title="Rhythm Activities for Third Grade",
            url="https://www.education.com/rhythm-activities-third-grade",
            snippet="Fun and educational rhythm activities specifically designed for third grade students.",
        ),
    ]

    # Create WebSearchContext
    context = WebSearchContext(
        query="third grade rhythm percussion lesson",
        results=results,
        total_results=len(results),
        search_time=0.5,
    )

    # Assign citation numbers
    context.assign_citation_numbers()
    print(f"Citation map: {context.citation_map}")

    # Generate bibliography
    bibliography = context.get_citation_bibliography()
    print(f"Bibliography:\n{bibliography}")

    return True


if __name__ == "__main__":
    print("🔍 Testing Citation System Fixes\n")

    try:
        # Test individual components
        test_search_result_citation()
        test_web_search_context_bibliography()

        print("\n✅ All citation system tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
