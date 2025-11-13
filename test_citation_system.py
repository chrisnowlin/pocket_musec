"""Test script to validate the citation system implementation"""

import asyncio
import logging
from backend.services.web_search_service import WebSearchService, SearchResult, WebSearchContext
from backend.llm.prompt_templates import LessonPromptTemplates, LessonPromptContext
from backend.citations.citation_formatter import CitationFormatter, CitationStyle
from backend.citations.citation_tracker import CitationTracker, SourceReference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_search_result_citation():
    """Test 1: SearchResult citation generation"""
    print("\n" + "="*80)
    print("TEST 1: SearchResult Citation Generation")
    print("="*80)
    
    try:
        result = SearchResult(
            title="Music Education Best Practices",
            url="https://nafme.org/music-education-practices",
            snippet="Comprehensive guide to effective music teaching strategies...",
            relevance_score=0.95,
            educational_domain=True
        )
        
        # Check citation ID generation
        assert result.citation_id is not None, "Citation ID not generated"
        print(f"✓ Citation ID generated: {result.citation_id}")
        
        # Check citation format
        citation_text = result.to_citation_format(1)
        assert "[1]" in citation_text, "Citation number not in format"
        assert result.title in citation_text, "Title not in citation"
        assert result.url in citation_text, "URL not in citation"
        print(f"✓ Citation format: {citation_text}")
        
        # Check context with citation
        context = result.to_context_with_citation(1)
        assert "[Web Source: 1" in context, "Citation marker not in context"
        assert result.url in context, "URL not in context"
        print(f"✓ Context with citation includes proper markers")
        
        print("\n✅ TEST 1 PASSED: SearchResult citation generation working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST 1 ERROR: {e}")
        return False

def test_web_search_context_citations():
    """Test 2: WebSearchContext citation management"""
    print("\n" + "="*80)
    print("TEST 2: WebSearchContext Citation Management")
    print("="*80)
    
    try:
        # Create multiple search results
        results = [
            SearchResult(
                title="Elementary Music Teaching",
                url="https://example.org/elementary-music",
                snippet="Teaching strategies for young learners..."
            ),
            SearchResult(
                title="Rhythm Activities for Kids",
                url="https://example.edu/rhythm-activities",
                snippet="Engaging rhythm activities..."
            ),
            SearchResult(
                title="Music Assessment Methods",
                url="https://example.org/assessment",
                snippet="Effective assessment strategies..."
            )
        ]
        
        # Create search context
        context = WebSearchContext(
            query="music teaching strategies",
            results=results,
            total_results=3,
            search_time=0.5
        )
        
        # Check citation assignment
        context.assign_citation_numbers()
        assert len(context.citation_map) == 3, f"Expected 3 citations, got {len(context.citation_map)}"
        print(f"✓ Citation numbers assigned: {context.citation_map}")
        
        # Check citation number retrieval
        for result in results:
            num = context.get_citation_number(result.citation_id)
            assert num is not None, f"Citation number not found for {result.citation_id}"
            print(f"✓ Citation {num} assigned to: {result.title}")
        
        # Check formatted results with citations
        formatted = context.format_results_with_citations()
        assert len(formatted) == 3, f"Expected 3 formatted results, got {len(formatted)}"
        for i, formatted_result in enumerate(formatted, 1):
            assert f"[Web Source: {i}" in formatted_result, f"Citation marker missing in result {i}"
        print(f"✓ All results formatted with citation markers")
        
        # Check bibliography generation
        bibliography = context.get_citation_bibliography()
        assert "## Web Sources References" in bibliography, "Bibliography header missing"
        assert "[1]" in bibliography, "Citation [1] missing from bibliography"
        assert "[2]" in bibliography, "Citation [2] missing from bibliography"
        assert "[3]" in bibliography, "Citation [3] missing from bibliography"
        print(f"✓ Bibliography generated with all citations")
        
        print("\n✅ TEST 2 PASSED: WebSearchContext citation management working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST 2 ERROR: {e}")
        return False

def test_prompt_template_integration():
    """Test 3: Prompt template web search context formatting"""
    print("\n" + "="*80)
    print("TEST 3: Prompt Template Integration")
    print("="*80)
    
    try:
        # Create mock web search context
        web_search_context = [
            "[Web Source: 1 - nafme.org]\nTitle: Music Education Standards\nContent: National standards for music education...\nURL: https://nafme.org/standards\nRelevance: 0.95\nReference: [1]",
            "[Web Source: 2 - education.org]\nTitle: Assessment Strategies\nContent: Effective music assessment methods...\nURL: https://education.org/assessment\nRelevance: 0.88\nReference: [2]"
        ]
        
        # Test the formatting method
        formatted_xml = LessonPromptTemplates._format_web_search_context(web_search_context)
        
        # Check XML structure
        assert "<rag_web_search_context>" in formatted_xml, "XML wrapper missing"
        assert "<citation_guidance>" in formatted_xml, "Citation guidance missing"
        assert "Web sources include citation markers" in formatted_xml, "Citation guidance text missing"
        assert "<content>" in formatted_xml, "Content section missing"
        print(f"✓ XML structure correct")
        
        # Check citation markers in formatted context
        assert "[Web Source: 1" in formatted_xml, "Citation marker [1] missing"
        assert "[Web Source: 2" in formatted_xml, "Citation marker [2] missing"
        print(f"✓ Citation markers preserved in formatted context")
        
        # Test with LessonPromptContext
        context = LessonPromptContext(
            grade_level="Grade 3",
            strand_code="ML",
            strand_name="Music Literacy",
            strand_description="Reading and understanding music notation",
            standard_id="3.ML.1",
            standard_text="Students will read basic music notation",
            objectives=["Read quarter and eighth notes"],
            web_search_context=web_search_context
        )
        
        # Generate lesson plan prompt
        prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
        
        # Check that web search context is included
        assert "<rag_web_search_context>" in prompt, "Web search context not included in prompt"
        assert "citation_guidance" in prompt, "Citation guidance not in prompt"
        assert "[Web Source: 1" in prompt, "Web citation markers not in prompt"
        print(f"✓ Web search context correctly integrated into lesson plan prompt")
        
        print("\n✅ TEST 3 PASSED: Prompt template integration working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST 3 ERROR: {e}")
        return False

def test_citation_formatter_web_sources():
    """Test 4: CitationFormatter web source handling"""
    print("\n" + "="*80)
    print("TEST 4: CitationFormatter Web Source Handling")
    print("="*80)
    
    try:
        formatter = CitationFormatter(style=CitationStyle.IEEE)
        
        # Create web source reference (simulating SearchResult)
        web_source = SourceReference(
            source_type="web",
            source_id="web_1",
            source_title="Music Teaching Strategies for Elementary Students"
        )
        
        # Add domain and URL as attributes (if supported)
        web_source.domain = "nafme.org"
        web_source.url = "https://nafme.org/music-teaching-strategies"
        
        # Test citation formatting
        citation = formatter.format_reference(web_source, 1)
        
        # Check IEEE format for web sources
        assert "[1]" in citation, "Citation number missing"
        assert web_source.source_title in citation, "Title missing from citation"
        assert "nafme.org" in citation or web_source.url in citation, "Domain/URL missing from citation"
        print(f"✓ Web source citation formatted correctly: {citation}")
        
        # Test inline citation
        inline = formatter.format_inline_citation(1)
        assert inline == "[1]", f"Expected '[1]', got '{inline}'"
        print(f"✓ Inline citation formatted correctly: {inline}")
        
        # Test multiple citations
        inline_multi = formatter.format_inline_citations([1, 2, 3])
        assert "[1-3]" in inline_multi or "[1, 2, 3]" in inline_multi, f"Multiple citations not formatted correctly: {inline_multi}"
        print(f"✓ Multiple inline citations formatted correctly: {inline_multi}")
        
        print("\n✅ TEST 4 PASSED: CitationFormatter web source handling working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST 4 ERROR: {e}")
        return False

async def test_web_search_service_integration():
    """Test 5: WebSearchService integration (requires API key)"""
    print("\n" + "="*80)
    print("TEST 5: WebSearchService Integration")
    print("="*80)
    
    try:
        from backend.config import config
        
        # Check if API key is configured
        if not config.web_search.api_key:
            print("⚠️  SKIPPED: No API key configured for web search")
            return None
        
        # Create web search service
        service = WebSearchService()
        
        # Test search with citation support
        search_context = await service.search_educational_resources(
            query="elementary music rhythm activities",
            max_results=3,
            grade_level="Grade 3",
            subject="music"
        )
        
        if not search_context or not search_context.results:
            print("⚠️  WARNING: No search results returned")
            return None
        
        # Check citation assignments
        assert len(search_context.citation_map) > 0, "No citations assigned to search results"
        print(f"✓ Citations assigned to {len(search_context.citation_map)} results")
        
        # Check each result has citation
        for result in search_context.results:
            assert result.citation_id is not None, "Result missing citation_id"
            citation_num = search_context.get_citation_number(result.citation_id)
            assert citation_num is not None, f"Citation number not found for {result.citation_id}"
            print(f"✓ Result '{result.title[:50]}...' has citation [{citation_num}]")
        
        # Check formatted results
        formatted_results = search_context.format_results_with_citations()
        assert len(formatted_results) > 0, "No formatted results"
        for formatted in formatted_results:
            assert "[Web Source:" in formatted, "Citation marker missing from formatted result"
        print(f"✓ All {len(formatted_results)} results formatted with citations")
        
        # Check bibliography
        bibliography = search_context.get_citation_bibliography()
        assert "## Web Sources References" in bibliography, "Bibliography header missing"
        assert "[1]" in bibliography, "First citation missing from bibliography"
        print(f"✓ Bibliography generated successfully")
        
        print("\n✅ TEST 5 PASSED: WebSearchService integration working correctly")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST 5 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all citation system tests"""
    print("\n" + "="*80)
    print("CITATION SYSTEM VALIDATION TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Test 1: SearchResult citation generation
    results['SearchResult Citations'] = test_search_result_citation()
    
    # Test 2: WebSearchContext citation management
    results['WebSearchContext Management'] = test_web_search_context_citations()
    
    # Test 3: Prompt template integration
    results['Prompt Template Integration'] = test_prompt_template_integration()
    
    # Test 4: CitationFormatter web sources
    results['CitationFormatter Web Sources'] = test_citation_formatter_web_sources()
    
    # Test 5: WebSearchService integration (may be skipped if no API key)
    results['WebSearchService Integration'] = await test_web_search_service_integration()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result is True else ("❌ FAILED" if result is False else "⚠️  SKIPPED")
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    if failed > 0:
        print("\n❌ CITATION SYSTEM HAS ISSUES - See failed tests above")
        return False
    elif passed == total:
        print("\n✅ ALL TESTS PASSED - Citation system is working correctly")
        return True
    else:
        print("\n⚠️  SOME TESTS SKIPPED - Review skipped tests")
        return True

if __name__ == "__main__":
    asyncio.run(run_all_tests())