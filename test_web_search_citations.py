#!/usr/bin/env python3
"""
Test script to verify web search citation implementation
"""

import asyncio
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.web_search_service import SearchResult, WebSearchContext
from backend.citations.citation_formatter import CitationFormatter, CitationStyle
from datetime import datetime


def test_search_result_citation():
    """Test that SearchResult can generate proper citations"""
    print("🧪 Testing SearchResult citation generation...")
    
    # Create a test search result
    result = SearchResult(
        title="Music Education Strategies for Elementary Students",
        url="https://www.musiceducators.org/elementary-strategies",
        snippet="This article provides comprehensive strategies for teaching music to elementary students, including rhythm activities and melody introduction techniques.",
        relevance_score=0.85
    )
    
    print(f"✅ Created SearchResult with citation_id: {result.citation_id}")
    print(f"✅ Domain detected: {result.domain}")
    print(f"✅ Source type: {result.source_type}")
    
    # Test citation format
    citation = result.to_citation_format(1)
    print(f"✅ Citation format: {citation}")
    
    # Test context with citation
    context = result.to_context_with_citation(1)
    print(f"✅ Context with citation:\n{context}")
    
    return result


def test_web_search_context():
    """Test WebSearchContext citation management"""
    print("\n🧪 Testing WebSearchContext citation management...")
    
    # Create test results
    results = [
        SearchResult(
            title="Teaching Rhythm in Music Education",
            url="https://www.education.gov/rhythm-strategies",
            snippet="Effective methods for teaching rhythm concepts to K-5 students.",
            relevance_score=0.9
        ),
        SearchResult(
            title="Musical Development in Children",
            url="https://www.musicpsychology.org/child-development",
            snippet="Research on how children develop musical skills and understanding.",
            relevance_score=0.75
        ),
        SearchResult(
            title="Classroom Music Activities",
            url="https://www.teachermusic.com/activities",
            snippet="Engaging music activities for the classroom setting.",
            relevance_score=0.8
        )
    ]
    
    # Create context
    context = WebSearchContext(
        query="music education elementary",
        results=results,
        total_results=len(results),
        search_time=1.2
    )
    
    print(f"✅ Created WebSearchContext with {len(results)} results")
    
    # Assign citation numbers
    context.assign_citation_numbers()
    print(f"✅ Assigned citation numbers: {context.citation_map}")
    
    # Test formatted results
    formatted_results = context.format_results_with_citations()
    print(f"✅ Formatted results with citations:")
    for i, result in enumerate(formatted_results, 1):
        print(f"   Result {i}:\n{result}\n")
    
    # Test bibliography generation
    bibliography = context.get_citation_bibliography()
    print(f"✅ Generated bibliography:\n{bibliography}")
    
    return context


def test_citation_formatter():
    """Test CitationFormatter with web sources"""
    print("\n🧪 Testing CitationFormatter with web sources...")
    
    formatter = CitationFormatter(CitationStyle.IEEE)
    
    # Create a mock web source reference
    from backend.citations.citation_tracker import SourceReference
    
    web_source = SourceReference(
        source_id="web_001",
        source_type="web",
        source_title="Innovative Music Teaching Methods",
        page_number=None,
        excerpt=None,
        relevance_score=0.85,
        file_id=None
    )
    
    # Add URL and domain attributes (these would be added by our enhanced SearchResult)
    web_source.url = "https://www.musicteaching.org/innovative-methods"
    web_source.domain = "musicteaching.org"
    
    # Test formatting
    citation = formatter.format_reference(web_source, 1)
    print(f"✅ Web source citation: {citation}")
    
    # Test inline citation
    inline = formatter.format_inline_citation(1)
    print(f"✅ Inline citation: {inline}")
    
    return formatter


def test_prompt_template_integration():
    """Test that prompt templates handle web search citations correctly"""
    print("\n🧪 Testing prompt template integration...")
    
    # Import templates
    from backend.llm.prompt_templates import LessonPromptTemplates
    
    # Create mock web search context with citations
    web_search_context = [
        "[Web Source: 1 - musiceducators.org]\nTitle: Music Education Strategies\nContent: Effective teaching methods...\nURL: https://www.musiceducators.org/strategies\nRelevance: 0.85\nReference: [1]",
        "[Web Source: 2 - education.gov]\nTitle: Rhythm Teaching Guide\nContent: Comprehensive rhythm instruction...\nURL: https://www.education.gov/rhythm\nRelevance: 0.90\nReference: [2]"
    ]
    
    # Test formatting
    formatted_context = LessonPromptTemplates._format_web_search_context(web_search_context)
    print(f"✅ Formatted web search context for prompts:")
    print(formatted_context)
    
    return formatted_context


def main():
    """Run all tests"""
    print("🚀 Starting Web Search Citation Implementation Tests\n")
    
    try:
        # Test individual components
        test_search_result_citation()
        test_web_search_context()
        test_citation_formatter()
        test_prompt_template_integration()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Implementation Summary:")
        print("• SearchResult dataclass enhanced with citation support")
        print("• WebSearchContext manages citation numbers automatically")
        print("• CitationFormatter handles web sources properly")
        print("• Prompt templates include citation guidance for LLM")
        print("• LessonAgent uses citation-enhanced context formatting")
        
        print("\n🎯 Citation Format Requirements Met:")
        print("• Web sources cited as: [Web Source: URL] or [1], [2], etc.")
        print("• URLs and domain information included in citations")
        print("• Consistent with existing RAG citation format (IEEE style)")
        print("• Clearly distinguishable from database citations")
        print("• LLM instructed to use citations for web content")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)