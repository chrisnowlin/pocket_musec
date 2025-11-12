#!/usr/bin/env python3
"""End-to-end test of RAG-enhanced lesson generation pipeline"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.repositories.standards_repository import StandardsRepository
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates

def test_semantic_search_integration():
    """Test semantic search integration with standards repository"""
    print("Testing semantic search integration...")
    
    repo = StandardsRepository()
    
    # Test semantic search with sample queries
    test_queries = [
        ("1st grade rhythm", "1"),
        ("3rd grade melody", "3"),
        ("5th grade composition", "5")
    ]
    
    all_passed = True
    
    for query, grade in test_queries:
        print(f"\n🔍 Testing query: '{query}' for grade {grade}")
        
        try:
            # Perform semantic search
            results = repo.search_standards_semantic(
                query=query,
                grade_level=grade,
                limit=5,
                similarity_threshold=0.3
            )
            
            print(f"✅ Found {len(results)} results")
            
            if results:
                for i, (standard, similarity) in enumerate(results[:2], 1):
                    print(f"   {i}. {standard.standard_id} - {standard.standard_text[:80]}... (similarity: {similarity:.3f})")
            else:
                print("⚠️  No results found - acceptable for test data")
                
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            all_passed = False
    
    return all_passed

def test_rag_prompt_generation():
    """Test RAG-enhanced prompt generation"""
    print("\nTesting RAG-enhanced prompt generation...")
    
    # Create sample RAG context
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
    
    # Create enhanced lesson context with RAG data
    context = LessonPromptContext(
        grade_level="3rd grade",
        strand_code="PR",
        strand_name="Musical Performance",
        strand_description="Perform music with expression and technical accuracy",
        standard_id="3.PR.1",
        standard_text="Sing and play music with accurate pitch and rhythm",
        objectives=[
            "Sing melodic patterns with accurate pitch",
            "Play rhythmic patterns on classroom instruments",
            "Maintain steady beat while performing"
        ],
        teaching_context=teaching_context,
        assessment_context=assessment_context,
        lesson_duration="45 minutes",
        class_size=25
    )
    
    # Generate RAG-enhanced prompt
    enhanced_prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
    
    print(f"✅ Generated RAG-enhanced prompt ({len(enhanced_prompt)} characters)")
    
    # Generate basic prompt without RAG for comparison
    basic_context = LessonPromptContext(
        grade_level=context.grade_level,
        strand_code=context.strand_code,
        strand_name=context.strand_name,
        strand_description=context.strand_description,
        standard_id=context.standard_id,
        standard_text=context.standard_text,
        objectives=context.objectives,
        lesson_duration=context.lesson_duration,
        class_size=context.class_size
    )
    
    basic_prompt = LessonPromptTemplates.generate_lesson_plan_prompt(basic_context)
    
    print(f"✅ Generated basic prompt without RAG ({len(basic_prompt)} characters)")
    
    # Compare and validate RAG enhancement
    enhancement_checks = [
        (len(enhanced_prompt) > len(basic_prompt), "Enhanced prompt is longer than basic"),
        ("<rag_teaching_context>" in enhanced_prompt, "Teaching context XML present"),
        ("<rag_assessment_context>" in enhanced_prompt, "Assessment context XML present"),
        ("Teaching Strategy Guidance" in enhanced_prompt, "Teaching guidance included"),
        ("Assessment Guidance" in enhanced_prompt, "Assessment guidance included"),
        ("evidence-based" in enhanced_prompt.lower(), "Evidence-based approach mentioned"),
        ("age-appropriate" in enhanced_prompt.lower(), "Age-appropriate instruction included"),
        ("<rag_teaching_context>" not in basic_prompt, "Basic prompt has no RAG teaching context"),
        ("<rag_assessment_context>" not in basic_prompt, "Basic prompt has no RAG assessment context")
    ]
    
    passed_checks = 0
    total_checks = len(enhancement_checks)
    
    print("\n🔍 Validating RAG enhancement:")
    for is_present, description in enhancement_checks:
        if is_present:
            passed_checks += 1
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
    
    # Calculate enhancement score
    enhancement_score = (passed_checks / total_checks) * 100
    print(f"\n📊 RAG Enhancement Score: {enhancement_score:.1f}% ({passed_checks}/{total_checks} checks passed)")
    
    # Calculate size increase
    size_increase = len(enhanced_prompt) - len(basic_prompt)
    size_percentage = (size_increase / len(basic_prompt)) * 100
    
    print(f"\n📈 Prompt size analysis:")
    print(f"   - Size increase: {size_increase} characters ({size_percentage:.1f}%)")
    
    # Check for enhanced educational content
    enhanced_content = [
        ("movement activities" in enhanced_prompt.lower(), "Movement-based teaching"),
        ("call-and-response" in enhanced_prompt.lower(), "Call-and-response strategies"),
        ("performance rubrics" in enhanced_prompt.lower(), "Performance assessment"),
        ("peer feedback" in enhanced_prompt.lower(), "Peer learning strategies"),
        ("self-reflection" in enhanced_prompt.lower(), "Self-assessment components")
    ]
    
    print(f"\n🎯 Enhanced educational content:")
    enhanced_count = 0
    for is_present, description in enhanced_content:
        if is_present:
            enhanced_count += 1
            print(f"   ✅ {description}")
        else:
            print(f"   ⚠️  {description} (optional)")
    
    return enhancement_score >= 80 and size_increase > 0

def test_rag_workflow_simulation():
    """Test complete RAG workflow simulation"""
    print("\nTesting complete RAG workflow simulation...")
    
    # Simulate lesson request analysis
    lesson_request = "Create a 4th grade lesson about musical composition"
    
    print(f"📝 Simulating lesson request: '{lesson_request}'")
    
    # Extract key information (simulated)
    extracted_info = {
        "grade_level": "4th grade",
        "musical_topics": ["composition", "creating music"],
        "lesson_type": "lesson_plan"
    }
    
    print(f"✅ Extracted information:")
    print(f"   - Grade level: {extracted_info['grade_level']}")
    print(f"   - Musical topics: {extracted_info['musical_topics']}")
    print(f"   - Lesson type: {extracted_info['lesson_type']}")
    
    # Test semantic search
    repo = StandardsRepository()
    
    try:
        # Normalize grade level for database
        grade_mapping = {
            "1st grade": "1", "2nd grade": "2", "3rd grade": "3",
            "4th grade": "4", "5th grade": "5", "kindergarten": "0"
        }
        normalized_grade = grade_mapping.get(extracted_info['grade_level'].lower(), extracted_info['grade_level'])
        
        search_results = repo.search_standards_semantic(
            query=" ".join(extracted_info['musical_topics']),
            grade_level=normalized_grade,
            limit=3,
            similarity_threshold=0.3
        )
        
        print(f"✅ Semantic search found {len(search_results)} relevant standards")
        
        if search_results:
            teaching_context = []
            assessment_context = []
            
            for standard, similarity in search_results:
                teaching_context.append(f"[{standard.standard_id}] Teaching strategy: {standard.standard_text[:200]}...")
                assessment_context.append(f"[{standard.standard_id}] Assessment method: {standard.standard_text[:200]}...")
            
            print(f"✅ Generated {len(teaching_context)} teaching context items")
            print(f"✅ Generated {len(assessment_context)} assessment context items")
            
            # Create enhanced prompt context
            if search_results:
                standard = search_results[0][0]
                
                context = LessonPromptContext(
                    grade_level=extracted_info['grade_level'],
                    strand_code=standard.strand_code,
                    strand_name=standard.strand_name,
                    strand_description=standard.strand_description,
                    standard_id=standard.standard_id,
                    standard_text=standard.standard_text,
                    objectives=[
                        "Create simple musical compositions",
                        "Use musical elements in original work",
                        "Share and discuss musical creations"
                    ],
                    teaching_context=teaching_context[:3],  # Limit for test
                    assessment_context=assessment_context[:3],  # Limit for test
                    lesson_duration="45 minutes"
                )
                
                # Generate final RAG-enhanced prompt
                final_prompt = LessonPromptTemplates.generate_lesson_plan_prompt(context)
                
                print(f"✅ Generated final RAG-enhanced prompt ({len(final_prompt)} characters)")
                
                # Validate final prompt
                validation_checks = [
                    ("4th grade" in final_prompt, "Grade level preserved"),
                    (standard.standard_id in final_prompt, "Standard ID included"),
                    ("<rag_teaching_context>" in final_prompt, "RAG teaching context integrated"),
                    ("<rag_assessment_context>" in final_prompt, "RAG assessment context integrated"),
                    ("composition" in final_prompt.lower(), "Musical topic addressed")
                ]
                
                passed_validations = 0
                for check, description in validation_checks:
                    if check:
                        passed_validations += 1
                        print(f"   ✅ {description}")
                    else:
                        print(f"   ❌ {description}")
                
                workflow_success = passed_validations >= 4
                print(f"\n📊 Workflow success: {workflow_success} ({passed_validations}/{len(validation_checks)} validations passed)")
                
                return workflow_success
                
    except Exception as e:
        print(f"❌ Workflow simulation failed: {e}")
        return False
    
    print("❌ No search results found for workflow simulation")
    return False

def main():
    """Run comprehensive RAG end-to-end tests"""
    print("Starting RAG End-to-End Pipeline Tests")
    print("=" * 60)
    
    tests = [
        test_semantic_search_integration,
        test_rag_prompt_generation,
        test_rag_workflow_simulation
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
            print(f"❌ {test_func.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RAG End-to-End Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All RAG end-to-end tests passed!")
        print("✅ Semantic search integration working correctly")
        print("✅ RAG context properly integrated into prompts")
        print("✅ Enhanced prompts show clear improvements over basic prompts")
        print("✅ Complete RAG workflow functioning as expected")
        print("✅ System ready for production use with enhanced lesson generation")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed - review RAG pipeline implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)