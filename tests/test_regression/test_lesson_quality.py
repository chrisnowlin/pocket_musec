#!/usr/bin/env python3
"""Regression tests for lesson generation quality"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any
import pytest

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.standards_fixtures import (
    get_standards_fixture, 
    get_lesson_fixture, 
    get_generated_lesson_fixture
)


class TestLessonQuality:
    """Regression tests to ensure lesson generation quality is maintained"""
    
    def test_lesson_contains_required_sections(self):
        """Test that generated lessons contain all required sections"""
        
        print("\n🧪 Testing Required Lesson Sections...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        required_sections = [
            "## Grade Level",
            "## Strand", 
            "## Standard",
            "## Learning Objectives",
            "## Lesson Activities",
            "## Assessment"
        ]
        
        for section in required_sections:
            assert section in lesson, f"Missing required section: {section}"
            print(f"✅ Found required section: {section}")
    
    def test_learning_objectives_are_measurable(self):
        """Test that learning objectives use measurable action verbs"""
        
        print("\n🧪 Testing Measurable Learning Objectives...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Extract learning objectives section
        objectives_match = re.search(r"## Learning Objectives\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        assert objectives_match, "Could not find Learning Objectives section"
        
        objectives_text = objectives_match.group(1)
        objective_lines = [line.strip() for line in objectives_text.split('\n') if line.strip().startswith(('Students will', 'Learners will'))]
        
        # Measurable action verbs (Bloom's Taxonomy)
        measurable_verbs = [
            'identify', 'describe', 'analyze', 'create', 'perform', 'demonstrate',
            'compare', 'evaluate', 'explain', 'apply', 'classify', 'compose',
            'improvise', 'interpret', 'recognize', 'differentiate', 'assess'
        ]
        
        non_measurable_patterns = [
            r'\bunderstand\b', r'\bknow\b', r'\blearn\b', r'\bappreciate\b',
            r'\benjoy\b', r'\bbe familiar with\b', r'\bbe aware of\b'
        ]
        
        for objective in objective_lines:
            # Check for measurable verbs
            has_measurable_verb = any(verb in objective.lower() for verb in measurable_verbs)
            
            # Check for non-measurable patterns
            has_non_measurable = any(re.search(pattern, objective.lower()) for pattern in non_measurable_patterns)
            
            assert has_measurable_verb, f"Objective may not be measurable: {objective}"
            assert not has_non_measurable, f"Objective uses non-measurable language: {objective}"
            
        print(f"✅ All {len(objective_lines)} objectives use measurable language")
    
    def test_lesson_includes_differentiation_strategies(self):
        """Test that lessons include differentiation for diverse learners"""
        
        print("\n🧪 Testing Differentiation Strategies...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for differentiation section
        differentiation_match = re.search(r"## Differentiation\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        assert differentiation_match, "Missing Differentiation section"
        
        differentiation_text = differentiation_match.group(1).lower()
        
        # Check for different types of differentiation
        differentiation_types = [
            'advanced', 'support', 'struggling', 'ell', 'english language learner',
            'gifted', 'special education', 'multiple levels'
        ]
        
        found_types = [dtype for dtype in differentiation_types if dtype in differentiation_text]
        assert len(found_types) >= 2, f"Should include differentiation for at least 2 learner types, found: {found_types}"
        
        print(f"✅ Found differentiation for: {', '.join(found_types)}")
    
    def test_lesson_includes_cross_curricular_connections(self):
        """Test that lessons include connections to other subject areas"""
        
        print("\n🧪 Testing Cross-Curricular Connections...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for cross-curricular section
        cross_curricular_match = re.search(r"## (Cross-Curricular|Integration|Connections)\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        
        if cross_curricular_match:
            cross_curricular_text = cross_curricular_match.group(1).lower()
            
            # Check for connections to core subjects
            subject_areas = [
                'math', 'language arts', 'science', 'social studies', 
                'history', 'geography', 'art', 'physical education', 'literature'
            ]
            
            found_subjects = [subject for subject in subject_areas if subject in cross_curricular_text]
            assert len(found_subjects) >= 1, f"Should include at least 1 cross-curricular connection"
            
            print(f"✅ Found cross-curricular connections to: {', '.join(found_subjects)}")
        else:
            print("⚠️  No explicit cross-curricular section found (may be integrated elsewhere)")
    
    def test_assessment_methods_are_varied(self):
        """Test that lessons include multiple assessment methods"""
        
        print("\n🧪 Testing Varied Assessment Methods...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for assessment section
        assessment_match = re.search(r"## Assessment\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        assert assessment_match, "Missing Assessment section"
        
        assessment_text = assessment_match.group(1).lower()
        
        # Check for different assessment types
        assessment_types = [
            'observation', 'performance', 'portfolio', 'rubric', 'self-assessment',
            'peer assessment', 'formative', 'summative', 'project', 'presentation',
            'discussion', 'participation', 'written', 'practical'
        ]
        
        found_types = [atype for atype in assessment_types if atype in assessment_text]
        assert len(found_types) >= 2, f"Should include at least 2 different assessment methods, found: {found_types}"
        
        print(f"✅ Found varied assessment methods: {', '.join(found_types)}")
    
    def test_lesson_activities_are_sequenced_logically(self):
        """Test that lesson activities follow logical sequence"""
        
        print("\n🧪 Testing Logical Activity Sequencing...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for activities section
        activities_match = re.search(r"## Lesson (Activities|Procedure)\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        assert activities_match, "Missing Lesson Activities section"
        
        activities_text = activities_match.group(1)
        
        # Check for logical flow indicators
        sequence_indicators = [
            'warm-up', 'introduction', 'demonstration', 'guided practice',
            'independent practice', 'creation', 'performance', 'closure',
            'reflection', 'assessment', 'evaluation'
        ]
        
        found_indicators = [indicator for indicator in sequence_indicators if indicator.lower() in activities_text.lower()]
        
        # Should have at least some logical sequence
        assert len(found_indicators) >= 3, f"Should include at least 3 sequential activity types, found: {found_indicators}"
        
        print(f"✅ Found logical sequence indicators: {', '.join(found_indicators)}")
    
    def test_lesson_includes_materials_and_resources(self):
        """Test that lessons list required materials and resources"""
        
        print("\n🧪 Testing Materials and Resources...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for materials section
        materials_match = re.search(r"## (Materials|Resources|Equipment)\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        assert materials_match, "Missing Materials/Resources section"
        
        materials_text = materials_match.group(1)
        
        # Check for specific material types
        material_types = [
            'instrument', 'recording', 'handout', 'worksheet', 'technology',
            'audio', 'visual', 'manipulative', 'equipment', 'software'
        ]
        
        found_types = [mtype for mtype in material_types if mtype.lower() in materials_text.lower()]
        assert len(found_types) >= 1, f"Should list at least 1 type of material/resource"
        
        print(f"✅ Found materials/resources: {', '.join(found_types)}")
    
    def test_standards_alignment_is_clear(self):
        """Test that lessons clearly align with specified standards"""
        
        print("\n🧪 Testing Standards Alignment...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Check that standard is mentioned in objectives and activities
        standard_match = re.search(r"## Standard\n(.*)", lesson)
        assert standard_match, "Missing Standard section"
        
        standard_text = standard_match.group(1).strip()
        
        # Extract standard ID
        standard_id_match = re.search(r"([A-Z]+\.\d+\.\d+\.\d+)", standard_text)
        if standard_id_match:
            standard_id = standard_id_match.group(1)
            
            # Check that standard ID is referenced elsewhere in lesson
            lesson_lower = lesson.lower()
            standard_parts = standard_id.split('.')
            
            # Should reference the strand or standard number in activities
            strand_reference = any(part.lower() in lesson_lower for part in standard_parts[:2])
            assert strand_reference, f"Lesson should reference standard {standard_id} in activities"
            
            print(f"✅ Lesson clearly aligns with standard: {standard_id}")
        else:
            print("⚠️  Could not extract standard ID format")
    
    def test_time_allocation_is_reasonable(self):
        """Test that lesson activities have reasonable time allocations"""
        
        print("\n🧪 Testing Time Allocation...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Look for time allocations in minutes
        time_matches = re.findall(r"\((\d+)\s*minutes?\)", lesson.lower())
        
        if time_matches:
            total_minutes = sum(int(minutes) for minutes in time_matches)
            
            # Should be reasonable for a class period (30-90 minutes typical)
            assert 30 <= total_minutes <= 180, f"Total lesson time {total_minutes} minutes seems unreasonable"
            
            print(f"✅ Reasonable time allocation: {total_minutes} minutes total")
        else:
            print("⚠️  No explicit time allocations found")
    
    def test_vocabulary_is_appropriate(self):
        """Test that lesson uses age-appropriate vocabulary"""
        
        print("\n🧪 Testing Age-Appropriate Vocabulary...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Extract grade level
        grade_match = re.search(r"## Grade Level\n(.*)", lesson)
        assert grade_match, "Missing Grade Level section"
        
        grade_text = grade_match.group(1).strip().lower()
        
        # Check for overly complex vocabulary in early grades
        if 'kindergarten' in grade_text or '1st grade' in grade_text or '2nd grade' in grade_text:
            complex_terms = [
                'pedagogy', 'methodology', 'theoretical framework', 'epistemology',
                'paradigm', 'socio-cultural', 'constructivist', 'behaviorist'
            ]
            
            found_complex = [term for term in complex_terms if term in lesson.lower()]
            assert len(found_complex) == 0, f"Found overly complex terms for early grades: {found_complex}"
            
            print("✅ Vocabulary is age-appropriate for grade level")
        else:
            print("✅ Grade level vocabulary check passed (upper grades)")
    
    def test_lesson_quality_score(self):
        """Calculate an overall lesson quality score"""
        
        print("\n🧪 Calculating Lesson Quality Score...")
        
        lesson = get_generated_lesson_fixture("detailed_lesson")
        
        quality_criteria = {
            "required_sections": 0,  # /20 points
            "measurable_objectives": 0,  # /15 points  
            "differentiation": 0,  # /15 points
            "assessment_variety": 0,  # /15 points
            "cross_curricular": 0,  # /10 points
            "materials_listed": 0,  # /10 points
            "logical_sequence": 0,  # /10 points
            "standards_alignment": 0,  # /5 points
        }
        
        # Required sections (20 points)
        required_sections = ["Grade Level", "Strand", "Standard", "Learning Objectives", "Activities", "Assessment"]
        found_sections = sum(1 for section in required_sections if f"## {section}" in lesson)
        quality_criteria["required_sections"] = (found_sections / len(required_sections)) * 20
        
        # Measurable objectives (15 points)
        objectives_match = re.search(r"## Learning Objectives\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        if objectives_match:
            objectives_text = objectives_match.group(1)
            measurable_verbs = ['identify', 'describe', 'analyze', 'create', 'perform', 'demonstrate']
            objective_lines = [line for line in objectives_text.split('\n') if 'Students will' in line]
            if objective_lines:
                measurable_count = sum(1 for obj in objective_lines if any(verb in obj.lower() for verb in measurable_verbs))
                quality_criteria["measurable_objectives"] = (measurable_count / len(objective_lines)) * 15
        
        # Differentiation (15 points)
        if "## Differentiation" in lesson:
            quality_criteria["differentiation"] = 15
        
        # Assessment variety (15 points)
        assessment_match = re.search(r"## Assessment\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        if assessment_match:
            assessment_types = ['observation', 'performance', 'rubric', 'self-assessment']
            found_types = sum(1 for atype in assessment_types if atype in assessment_match.group(1).lower())
            quality_criteria["assessment_variety"] = min((found_types / 3) * 15, 15)
        
        # Cross-curricular (10 points)
        if any(term in lesson.lower() for term in ['math', 'language arts', 'science', 'social studies']):
            quality_criteria["cross_curricular"] = 10
        
        # Materials (10 points)
        if "## Materials" in lesson or "## Resources" in lesson:
            quality_criteria["materials_listed"] = 10
        
        # Logical sequence (10 points)
        sequence_indicators = ['warm-up', 'introduction', 'practice', 'closure']
        found_indicators = sum(1 for indicator in sequence_indicators if indicator in lesson.lower())
        quality_criteria["logical_sequence"] = min((found_indicators / 3) * 10, 10)
        
        # Standards alignment (5 points)
        if re.search(r"[A-Z]+\.\d+\.\d+\.\d+", lesson):
            quality_criteria["standards_alignment"] = 5
        
        # Calculate total score
        total_score = sum(quality_criteria.values())
        max_score = 100
        
        print(f"📊 Lesson Quality Score: {total_score:.1f}/{max_score}")
        
        for criterion, score in quality_criteria.items():
            print(f"   {criterion}: {score:.1f}")
        
        # Should meet minimum quality threshold
        assert total_score >= 70, f"Lesson quality score {total_score} is below minimum threshold of 70"
        
        print(f"✅ Lesson meets quality standards")


class TestLessonRegression:
    """Regression tests to prevent quality degradation"""
    
    def test_minimal_lesson_quality_baseline(self):
        """Test that even minimal lessons meet basic quality standards"""
        
        print("\n🧪 Testing Minimal Lesson Quality Baseline...")
        
        lesson = get_generated_lesson_fixture("minimal_lesson")
        
        # Basic requirements that even minimal lessons should meet
        basic_requirements = [
            ("## Grade Level", "Grade level specified"),
            ("## Standard", "Standard specified"),
            ("## Objectives", "Learning objectives included"),
            ("## Activities", "Learning activities included"),
        ]
        
        for requirement, description in basic_requirements:
            assert requirement in lesson, f"Minimal lesson missing: {description}"
            print(f"✅ Basic requirement met: {description}")
        
        # Should have at least 2 learning objectives
        objectives_match = re.search(r"## Objectives\n(.*?)(?=\n##|\n$)", lesson, re.DOTALL)
        if objectives_match:
            objectives_text = objectives_match.group(1)
            objective_lines = [line.strip() for line in objectives_text.split('\n') if line.strip() and line.strip()[0].isdigit()]
            assert len(objective_lines) >= 2, f"Should have at least 2 objectives, found {len(objective_lines)}"
            print(f"✅ Has sufficient objectives: {len(objective_lines)}")
    
    def test_detailed_lesson_quality_improvement(self):
        """Test that detailed lessons show quality improvement over minimal ones"""
        
        print("\n🧪 Testing Detailed Lesson Quality Improvement...")
        
        minimal_lesson = get_generated_lesson_fixture("minimal_lesson")
        detailed_lesson = get_generated_lesson_fixture("detailed_lesson")
        
        # Detailed lesson should have more sections
        minimal_sections = len(re.findall(r"## [A-Z]", minimal_lesson))
        detailed_sections = len(re.findall(r"## [A-Z]", detailed_lesson))
        
        assert detailed_sections > minimal_sections, f"Detailed lesson should have more sections ({detailed_sections} vs {minimal_sections})"
        print(f"✅ Detailed lesson has more sections: {detailed_sections} vs {minimal_sections}")
        
        # Detailed lesson should be longer
        assert len(detailed_lesson) > len(minimal_lesson), "Detailed lesson should be longer"
        print(f"✅ Detailed lesson is more comprehensive: {len(detailed_lesson)} vs {len(minimal_lesson)} characters")
        
        # Detailed lesson should include more advanced elements
        advanced_elements = ["Differentiation", "Cross-Curricular", "Materials", "Integration"]
        found_advanced = sum(1 for element in advanced_elements if element in detailed_lesson)
        assert found_advanced >= 2, f"Detailed lesson should include advanced elements, found {found_advanced}"
        print(f"✅ Detailed lesson includes advanced elements: {found_advanced}")


if __name__ == "__main__":
    # Run tests manually if called directly
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLessonQuality)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLessonRegression))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)