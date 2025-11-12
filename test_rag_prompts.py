#!/usr/bin/env python3
"""Test RAG prompt generation and validation"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.llm.prompt_templates import LessonPromptTemplates, LessonPromptContext

def test_rag_prompt_validation():
    """Test RAG prompt validation"""
    print("Testing RAG prompt validation...")
    
    # Create sample context with RAG data
    teaching_context = [
        "Use movement activities to teach rhythm concepts",
        "Incorporate call-and-response patterns for engagement"
    ]
    
    assessment_context = [
        "Use performance rubrics with clear criteria",
        "Include self-reflection components"
    ]
    
    context = LessonPromptContext(
        grade_level="3rd grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="3.PR.1",
        standard_text="Sing and play music with accurate pitch and rhythm",
        objectives=[
            "Sing melodic patterns with accurate pitch",
            "Play rhythmic patterns on classroom instruments"
        ],
        teaching_context=teaching_context,
        assessment_context=assessment_context
    )
    
    # Generate lesson plan prompt
    prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
    
    print("✅ Generated RAG-enhanced lesson plan prompt")
    
    # Verify RAG elements are present
    rag_elements = [
        "<rag_teaching_context>",
        "<rag_assessment_context>",
        "Teaching Strategy Guidance",
        "Assessment Guidance",
        "evidence-based",
        "age-appropriate"
    ]
    
    missing_elements = []
    for element in rag_elements:
        if element not in prompt:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing RAG elements: {missing_elements}")
        return False
    else:
        print("✅ All RAG elements present in prompt")
    
    # Test backward compatibility - create context without RAG
    context_no_rag = LessonPromptContext(
        grade_level="5th grade",
        strand_code="CR",
        strand_name="Musical Creativity",
        strand_description="Create music through improvisation and composition",
        standard_id="5.CR.1",
        standard_text="Compose music using musical elements",
        objectives=[
            "Compose simple melodies",
            "Arrange musical ideas into a cohesive piece"
        ]
    )
    
    prompt_no_rag = LessonPromptTemplates.generate_lesson_plan_prompt(context_no_rag)
    
    print("✅ Generated backward-compatible prompt without RAG")
    
    # Verify no RAG elements in backward compatibility test
    unwanted_rag = [
        "<rag_teaching_context>",
        "<rag_assessment_context>",
        "Teaching Strategy Guidance",
        "RAG context"
    ]
    
    found_unwanted = []
    for element in unwanted_rag:
        if element in prompt_no_rag:
            found_unwanted.append(element)
    
    if found_unwanted:
        print(f"❌ Found unwanted RAG elements: {found_unwanted}")
        return False
    else:
        print("✅ Backward compatibility maintained - no unwanted RAG elements")
    
    return True

def test_multiple_prompt_types():
    """Test RAG integration in multiple prompt types"""
    print("\nTesting RAG integration in multiple prompt types...")
    
    teaching_context = ["Use movement activities to teach rhythm"]
    assessment_context = ["Use performance rubrics with clear criteria"]
    
    context = LessonPromptContext(
        grade_level="2nd grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="2.PR.1",
        standard_text="Sing and play music with accurate pitch and rhythm",
        objectives=["Sing melodic patterns with accurate pitch"],
        teaching_context=teaching_context,
        assessment_context=assessment_context
    )
    
    # Test different prompt types
    prompt_types = [
        ("lesson_plan", LessonPromptTemplates.generate_lesson_plan_prompt),
        ("activity_ideas", LessonPromptTemplates.generate_activity_ideas_prompt),
        ("assessment", LessonPromptTemplates.generate_assessment_prompt)
    ]
    
    for prompt_name, prompt_func in prompt_types:
        prompt = prompt_func(context)
        
        if "<rag_teaching_context>" in prompt and "<rag_assessment_context>" in prompt:
            print(f"✅ {prompt_name} prompt includes RAG context")
        else:
            print(f"❌ {prompt_name} prompt missing RAG context")
            return False
    
    return True

def main():
    """Run RAG prompt validation tests"""
    print("Starting RAG Prompt Validation Tests")
    print("=" * 50)
    
    tests = [
        test_rag_prompt_validation,
        test_multiple_prompt_types
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"RAG Prompt Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All RAG prompt tests passed!")
        print("✅ RAG context properly integrated into prompts")
        print("✅ Backward compatibility maintained")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)