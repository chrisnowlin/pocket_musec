#!/usr/bin/env python3
"""Test prompt generation with RAG context integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.llm.prompt_templates import LessonPromptTemplates, LessonPromptContext

def test_rag_context_formatting():
    """Test the RAG context formatting helper method"""
    print("Testing RAG context formatting...")
    
    # Test with both teaching and assessment context
    teaching_context = [
        "Use movement activities to teach rhythm concepts",
        "Incorporate call-and-response patterns for engagement",
        "Provide visual aids for musical notation"
    ]
    
    assessment_context = [
        "Use performance rubrics with clear criteria",
        "Implement peer feedback opportunities",
        "Include self-reflection components"
    ]
    
    formatted = LessonPromptTemplates._format_rag_context(
        teaching_context=teaching_context,
        assessment_context=assessment_context
    )
    
    print("Formatted RAG Context:")
    print("=" * 50)
    print(formatted)
    print("=" * 50)
    
    # Verify XML structure
    assert "<rag_teaching_context>" in formatted
    assert "<rag_assessment_context>" in formatted
    assert "<header>Teaching Strategies and Pedagogical Content</header>" in formatted
    assert "<header>Assessment Strategies and Guidance</header>" in formatted
    assert "index='1'" in formatted
    assert "index='2'" in formatted
    assert "index='3'" in formatted
    
    print("✅ RAG context formatting test passed")
    return True

def test_lesson_plan_prompt_with_rag():
    """Test lesson plan prompt generation with RAG context"""
    print("\nTesting lesson plan prompt with RAG context...")
    
    # Create context with RAG data
    context = LessonPromptContext(
        grade_level="1st grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="1.PR.2",
        standard_text="Execute rhythmic patterns using body percussion and instruments",
        objectives=[
            "Perform steady beat using body percussion",
            "Execute simple rhythmic patterns",
            "Maintain tempo while performing"
        ],
        teaching_context=[
            "Use movement activities to teach rhythm concepts",
            "Incorporate call-and-response patterns for engagement" 
        ],
        assessment_context=[
            "Use performance rubrics with clear criteria",
            "Include self-reflection components"
        ]
    )
    
    prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
    
    print("Lesson Plan Prompt (first 1000 chars):")
    print("=" * 50)
    print(prompt[:1000])
    print("=" * 50)
    
    # Verify RAG integration
    assert "<rag_teaching_context>" in prompt
    assert "<rag_assessment_context>" in prompt
    assert "Integrate proven teaching strategies from educational resources provided" in prompt
    assert "Incorporate evidence-based assessment methods from expert guidance" in prompt
    assert "Teaching Strategy Guidance" in prompt
    assert "Assessment Guidance" in prompt
    
    print("✅ Lesson plan prompt with RAG test passed")
    return True

def test_lesson_plan_prompt_without_rag():
    """Test lesson plan prompt generation without RAG context (backward compatibility)"""
    print("\nTesting lesson plan prompt without RAG context...")
    
    # Create context without RAG data
    context = LessonPromptContext(
        grade_level="3rd grade",
        strand_code="CR",
        strand_name="Musical Creativity",
        strand_description="Create music through improvisation and composition",
        standard_id="3.CR.1",
        standard_text="Improvise rhythmic and melodic patterns",
        objectives=[
            "Improvise simple rhythmic patterns",
            "Create melodic variations"
        ]
        # No teaching_context or assessment_context
    )
    
    prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
    
    print("Lesson Plan Prompt without RAG (first 800 chars):")
    print("=" * 50)
    print(prompt[:800])
    print("=" * 50)
    
    # Verify no RAG content
    assert "<rag_teaching_context>" not in prompt
    assert "<rag_assessment_context>" not in prompt
    assert "Teaching Strategy Guidance" not in prompt
    assert "Assessment Guidance" not in prompt
    assert "RAG context" not in prompt.lower()
    
    # Verify standard content is still there
    assert "Create a detailed lesson plan that directly addresses the standard" in prompt
    assert "3.CR.1" in prompt
    assert "3rd grade" in prompt
    
    print("✅ Backward compatibility test passed")
    return True

def test_activity_ideas_prompt_with_rag():
    """Test activity ideas prompt with RAG context"""
    print("\nTesting activity ideas prompt with RAG context...")
    
    context = LessonPromptContext(
        grade_level="2nd grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="2.PR.1",
        standard_text="Sing and play music with accurate pitch and rhythm",
        objectives=[
            "Sing melodic patterns with accurate pitch",
            "Play rhythmic patterns on classroom instruments"
        ],
        teaching_context=[
            "Use movement activities to teach rhythm concepts",
            "Incorporate call-and-response patterns for engagement"
        ]
    )
    
    prompt = LessonPromptTemplates.generate_activity_ideas_prompt(context)
    
    print("Activity Ideas Prompt with RAG (first 800 chars):")
    print("=" * 50)
    print(prompt[:800])
    print("=" * 50)
    
    # Verify RAG integration for activities
    assert "<rag_teaching_context>" in prompt
    assert "Teaching Strategy Integration" in prompt
    assert "Integration of evidence-based teaching strategies (from RAG context)" in prompt
    assert "RAG Integration:" in prompt  # in the format section
    
    print("✅ Activity ideas prompt with RAG test passed")
    return True

def test_assessment_prompt_with_rag():
    """Test assessment strategies prompt with RAG context"""
    print("\nTesting assessment strategies prompt with RAG context...")
    
    context = LessonPromptContext(
        grade_level="4th grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="4.PR.2",
        standard_text="Perform music with appropriate expression and technique",
        objectives=[
            "Demonstrate expressive qualities in performance",
            "Apply technical accuracy to musical passages"
        ],
        assessment_context=[
            "Use performance rubrics with clear criteria",
            "Implement peer feedback opportunities",
            "Include self-reflection components"
        ]
    )
    
    prompt = LessonPromptTemplates.generate_assessment_prompt(context)
    
    print("Assessment Prompt with RAG (first 800 chars):")
    print("=" * 50)
    print(prompt[:800])
    print("=" * 50)
    
    # Verify RAG integration for assessment
    assert "<rag_assessment_context>" in prompt
    assert "Assessment Strategy Integration" in prompt
    assert "Integration of evidence-based assessment methods (from RAG context)" in prompt
    
    print("✅ Assessment strategies prompt with RAG test passed")
    return True

def test_comprehensive_lesson_prompt_with_rag():
    """Test comprehensive lesson prompt with RAG context"""
    print("\nTesting comprehensive lesson prompt with RAG context...")
    
    context = LessonPromptContext(
        grade_level="5th grade",
        strand_code="CR",
        strand_name="Musical Creativity",
        strand_description="Create music through improvisation and composition",
        standard_id="5.CR.1",
        standard_text="Compose music using musical elements",
        objectives=[
            "Compose simple melodies",
            "Arrange musical ideas into a cohesive piece"
        ],
        teaching_context=[
            "Use movement activities to teach rhythm concepts",
            "Provide visual aids for musical notation"
        ],
        assessment_context=[
            "Use performance rubrics with clear criteria",
            "Include self-reflection components"
        ]
    )
    
    prompt = LessonPromptTemplates.create_comprehensive_lesson_prompt(context)
    
    print("Comprehensive Lesson Prompt with RAG (first 1000 chars):")
    print("=" * 50)
    print(prompt[:1000])
    print("=" * 50)
    
    # Verify comprehensive RAG integration
    assert "<rag_teaching_context>" in prompt
    assert "<rag_assessment_context>" in prompt
    assert "Comprehensive Teaching Integration" in prompt
    assert "Comprehensive Assessment Integration" in prompt
    assert "9. Integration of evidence-based teaching strategies from RAG context" in prompt
    assert "10. Application of research-supported assessment methods from RAG context" in prompt
    
    print("✅ Comprehensive lesson prompt with RAG test passed")
    return True

def main():
    """Run all prompt RAG integration tests"""
    print("Starting Prompt RAG Integration Tests")
    print("=" * 60)
    
    tests = [
        test_rag_context_formatting,
        test_lesson_plan_prompt_with_rag,
        test_lesson_plan_prompt_without_rag,
        test_activity_ideas_prompt_with_rag,
        test_assessment_prompt_with_rag,
        test_comprehensive_lesson_prompt_with_rag
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Prompt RAG Integration Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All prompt RAG integration tests passed!")
        print("✅ RAG context is properly formatted and integrated into prompts")
        print("✅ Backward compatibility is maintained for non-RAG prompts")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed - check prompt template implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)