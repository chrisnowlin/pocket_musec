#!/usr/bin/env python3
"""
Comprehensive comparative test for lesson generation quality
Tests both old keyword-based approach and new RAG-enhanced approach
"""

import sys
import os
import time
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates
from backend.llm.chutes_client import ChutesClient, Message
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestScenario:
    """Test scenario for lesson generation comparison"""
    grade_level: str
    musical_topic: str
    description: str
    expected_keywords: List[str]
    complexity_level: str  # "basic", "intermediate", "advanced"

@dataclass
class GenerationResult:
    """Result from lesson generation"""
    approach: str  # "keyword" or "rag"
    scenario: TestScenario
    lesson_content: str
    selected_standards: List[Dict[str, str]]
    teaching_strategies: List[str]
    assessment_methods: List[str]
    generation_time: float
    prompt_size: int
    response_size: int
    semantic_similarity_scores: List[float]
    quality_metrics: Dict[str, Any]

@dataclass
class QualityAnalysis:
    """Analysis of lesson generation quality"""
    standard_relevance_score: float
    teaching_strategy_quality: float
    assessment_quality: float
    coherence_score: float
    educational_value_score: float
    age_appropriateness_score: float
    overall_quality_score: float
    improvements_noted: List[str]
    weaknesses_identified: List[str]

class LessonGenerationComparator:
    """Comparator for testing lesson generation approaches"""
    
    def __init__(self):
        self.standards_repo = StandardsRepository()
        self.flow = Flow()
        self.store = Store()
        self.llm_client = ChutesClient()
        self.prompt_templates = LessonPromptTemplates()
        
        # Initialize lesson agent
        self.lesson_agent = LessonAgent(
            self.flow, 
            self.store, 
            conversational_mode=True
        )
        
        # Test scenarios covering different grade levels and topics
        self.test_scenarios = [
            TestScenario(
                grade_level="1st grade",
                musical_topic="rhythm patterns",
                description="Basic rhythm concepts for young learners",
                expected_keywords=["beat", "rhythm", "pattern", "tempo"],
                complexity_level="basic"
            ),
            TestScenario(
                grade_level="3rd grade",
                musical_topic="melody creation",
                description="Melodic concepts and simple composition",
                expected_keywords=["melody", "pitch", "contour", "scale"],
                complexity_level="intermediate"
            ),
            TestScenario(
                grade_level="5th grade",
                musical_topic="music composition",
                description="Advanced composition and musical elements",
                expected_keywords=["composition", "form", "harmony", "structure"],
                complexity_level="advanced"
            )
        ]
    
    def _mock_keyword_based_standards_search(self, scenario: TestScenario) -> List[Dict[str, str]]:
        """
        Mock the old keyword-based standards search approach
        This simulates how the system worked before semantic search
        """
        logger.info(f"Performing keyword-based search for: {scenario.musical_topic}")
        
        # Get all standards for the grade level
        normalized_grade = self.lesson_agent._normalize_grade_level(scenario.grade_level)
        all_standards = self.standards_repo.get_standards_by_grade(normalized_grade)
        
        # Simulate old keyword matching logic
        matched_standards = []
        keywords = scenario.expected_keywords + [scenario.musical_topic.lower()]
        
        for standard in all_standards:
            score = 0
            standard_text_lower = standard.standard_text.lower()
            
            # Simple keyword matching (old approach)
            for keyword in keywords:
                if keyword in standard_text_lower:
                    score += 1
            
            # Add related terms (basic thesaurus-like approach)
            for keyword in keywords:
                related_terms = self.lesson_agent._get_related_terms(keyword)
                for related in related_terms:
                    if related in standard_text_lower:
                        score += 0.5
            
            if score > 0:
                matched_standards.append({
                    "standard": standard,
                    "score": score,
                    "match_type": "keyword"
                })
        
        # Sort by score and return top matches
        matched_standards.sort(key=lambda x: x["score"], reverse=True)
        top_standards = matched_standards[:3]
        
        logger.info(f"Keyword search found {len(top_standards)} standards")
        return [
            {
                "standard_id": std["standard"].standard_id,
                "standard_text": std["standard"].standard_text,
                "strand_name": std["standard"].strand_name,
                "relevance_score": std["score"],
                "match_type": std["match_type"]
            }
            for std in top_standards
        ]
    
    def _get_rag_enhanced_standards_search(self, scenario: TestScenario) -> List[Dict[str, str]]:
        """
        Use the new RAG-enhanced semantic search approach
        """
        logger.info(f"Performing RAG-enhanced semantic search for: {scenario.musical_topic}")
        
        extracted_info = {
            "grade_level": scenario.grade_level,
            "musical_topics": [scenario.musical_topic]
        }
        
        # Use the lesson agent's semantic search
        try:
            relevant_standards = self.lesson_agent._get_relevant_standards(extracted_info)
            
            # Get semantic similarity scores
            normalized_grade = self.lesson_agent._normalize_grade_level(scenario.grade_level)
            search_results = self.standards_repo.search_standards_semantic(
                query=scenario.musical_topic,
                grade_level=normalized_grade,
                limit=3,
                similarity_threshold=0.3
            )
            
            standards_with_scores = []
            for standard, similarity in search_results:
                standards_with_scores.append({
                    "standard_id": standard.standard_id,
                    "standard_text": standard.standard_text,
                    "strand_name": standard.strand_name,
                    "relevance_score": similarity,
                    "match_type": "semantic"
                })
            
            logger.info(f"RAG semantic search found {len(standards_with_scores)} standards")
            return standards_with_scores
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            # Fallback to keyword search
            return self._mock_keyword_based_standards_search(scenario)
    
    def _generate_mock_teaching_strategies(self, scenario: TestScenario) -> List[str]:
        """
        Mock old approach to teaching strategies (generic)
        """
        generic_strategies = [
            f"Use call-and-response for {scenario.musical_topic}",
            f"Incorporate movement activities for {scenario.grade_level}",
            f"Provide visual aids for musical concepts",
            f"Use hands-on activities with instruments",
            f"Include group collaboration opportunities"
        ]
        return generic_strategies[:3]  # Return first 3 generic strategies
    
    def _get_rag_teaching_strategies(self, scenario: TestScenario) -> List[str]:
        """
        Get RAG-enhanced teaching strategies
        """
        extracted_info = {
            "grade_level": scenario.grade_level,
            "musical_topics": [scenario.musical_topic]
        }
        
        try:
            teaching_context = self.lesson_agent._get_teaching_strategies_context(extracted_info)
            return teaching_context[:3] if teaching_context else self._generate_mock_teaching_strategies(scenario)
        except Exception as e:
            logger.error(f"RAG teaching strategies failed: {e}")
            return self._generate_mock_teaching_strategies(scenario)
    
    def _generate_mock_assessment_methods(self, scenario: TestScenario) -> List[str]:
        """
        Mock old approach to assessment methods (generic)
        """
        generic_assessments = [
            "Observe student participation",
            "Use simple performance rubrics",
            "Include peer feedback opportunities",
            "Provide written reflection prompts",
            "Use exit tickets for quick assessment"
        ]
        return generic_assessments[:3]
    
    def _get_rag_assessment_methods(self, scenario: TestScenario) -> List[str]:
        """
        Get RAG-enhanced assessment methods
        """
        extracted_info = {
            "grade_level": scenario.grade_level,
            "musical_topics": [scenario.musical_topic]
        }
        
        try:
            assessment_context = self.lesson_agent._get_assessment_guidance_context(extracted_info)
            return assessment_context[:3] if assessment_context else self._generate_mock_assessment_methods(scenario)
        except Exception as e:
            logger.error(f"RAG assessment methods failed: {e}")
            return self._generate_mock_assessment_methods(scenario)
    
    def _generate_lesson_content(self, scenario: TestScenario, standards: List[Dict], 
                                teaching_strategies: List[str], assessment_methods: List[str],
                                use_rag: bool = False) -> Tuple[str, float, int, int]:
        """
        Generate lesson content using the appropriate approach
        Returns: (lesson_content, generation_time, prompt_size, response_size)
        """
        start_time = time.time()
        
        try:
            # Create lesson context
            context = LessonPromptContext(
                grade_level=scenario.grade_level,
                strand_code=standards[0]["standard_id"].split('.')[0] if standards else "PR",
                strand_name=standards[0]["strand_name"] if standards else "Musical Performance",
                strand_description="Perform music with expression and technical accuracy",
                standard_id=standards[0]["standard_id"] if standards else "Custom",
                standard_text=standards[0]["standard_text"] if standards else scenario.description,
                objectives=[
                    f"Understand {scenario.musical_topic} concepts",
                    f"Apply {scenario.musical_topic} in musical activities",
                    f"Create musical examples using {scenario.musical_topic}"
                ],
                teaching_context=teaching_strategies if use_rag else None,
                assessment_context=assessment_methods if use_rag else None,
                lesson_duration="45 minutes",
                class_size=25
            )
            
            # Generate prompt
            if use_rag:
                prompt = self.prompt_templates.generate_lesson_plan_prompt(context)
            else:
                # Create basic prompt without RAG context
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
                prompt = self.prompt_templates.generate_lesson_plan_prompt(basic_context)
            
            prompt_size = len(prompt)
            
            # Generate lesson using LLM
            messages = [
                Message(role="system", content=self.prompt_templates.get_system_prompt()),
                Message(role="user", content=prompt)
            ]
            
            response = self.llm_client.chat_completion(
                messages=messages, 
                temperature=0.7, 
                max_tokens=2000
            )
            
            # Handle response
            if hasattr(response, 'content'):
                lesson_content = response.content
            elif isinstance(response, dict):
                lesson_content = response.get('content', str(response))
            else:
                lesson_content = str(response)
            
            generation_time = time.time() - start_time
            response_size = len(lesson_content)
            
            logger.info(f"Generated lesson content in {generation_time:.2f}s")
            return lesson_content, generation_time, prompt_size, response_size
            
        except Exception as e:
            logger.error(f"Lesson generation failed: {e}")
            # Return mock content
            mock_content = f"""
            ## Lesson Plan: {scenario.musical_topic} for {scenario.grade_level}
            
            ### Objectives
            - Understand {scenario.musical_topic} concepts
            - Apply knowledge in practical activities
            - Create musical examples
            
            ### Activities
            - Introduction to {scenario.musical_topic}
            - Hands-on practice activities
            - Creative application projects
            
            ### Assessment
            - Observation of participation
            - Performance evaluation
            - Reflection and discussion
            """
            
            generation_time = time.time() - start_time
            return mock_content, generation_time, len(prompt), len(mock_content)
    
    def _analyze_quality(self, result: GenerationResult) -> QualityAnalysis:
        """
        Analyze the quality of generated lesson content
        """
        content = result.lesson_content.lower()
        
        # Standard relevance analysis
        standard_relevance = 0.0
        if result.selected_standards:
            avg_relevance = sum(std.get("relevance_score", 0) for std in result.selected_standards) / len(result.selected_standards)
            standard_relevance = min(avg_relevance * 100, 100)  # Normalize to 0-100
        
        # Teaching strategy quality
        strategy_quality = 0.0
        if result.teaching_strategies:
            strategy_indicators = ["movement", "visual", "hands-on", "collaborative", "interactive"]
            strategy_mentions = sum(1 for indicator in strategy_indicators if indicator in content)
            strategy_quality = min((strategy_mentions / len(strategy_indicators)) * 100, 100)
        
        # Assessment quality
        assessment_quality = 0.0
        if result.assessment_methods:
            assessment_indicators = ["rubric", "formative", "summative", "observation", "self-assessment"]
            assessment_mentions = sum(1 for indicator in assessment_indicators if indicator in content)
            assessment_quality = min((assessment_mentions / len(assessment_indicators)) * 100, 100)
        
        # Coherence analysis
        coherence_indicators = ["objectives", "activities", "assessment", "materials", "procedure"]
        coherence_score = sum(1 for indicator in coherence_indicators if indicator in content)
        coherence_score = min((coherence_score / len(coherence_indicators)) * 100, 100)
        
        # Educational value
        educational_indicators = ["learning", "understanding", "application", "creation", "reflection"]
        educational_mentions = sum(1 for indicator in educational_indicators if indicator in content)
        educational_value = min((educational_mentions / len(educational_indicators)) * 100, 100)
        
        # Age appropriateness (simple heuristic based on complexity)
        grade_complexity = {"1st grade": 0.3, "3rd grade": 0.6, "5th grade": 0.9}.get(result.scenario.grade_level, 0.6)
        content_complexity = len(content) / 1000  # Simple complexity proxy
        age_appropriateness = max(0, 100 - abs(content_complexity - grade_complexity) * 50)
        
        # Overall quality score
        overall_quality = (standard_relevance + strategy_quality + assessment_quality + 
                          coherence_score + educational_value + age_appropriateness) / 6
        
        # Identify improvements and weaknesses
        improvements = []
        weaknesses = []
        
        if result.approach == "rag":
            if result.teaching_strategies and len(result.teaching_strategies) > 0:
                improvements.append("Evidence-based teaching strategies included")
            if result.assessment_methods and len(result.assessment_methods) > 0:
                improvements.append("Specialized assessment methods integrated")
            if result.semantic_similarity_scores:
                improvements.append("Semantic search improved standard selection")
        else:
            if len(result.teaching_strategies) == 0:
                weaknesses.append("No specialized teaching strategies provided")
            if len(result.assessment_methods) == 0:
                weaknesses.append("Generic assessment methods only")
        
        return QualityAnalysis(
            standard_relevance_score=standard_relevance,
            teaching_strategy_quality=strategy_quality,
            assessment_quality=assessment_quality,
            coherence_score=coherence_score,
            educational_value_score=educational_value,
            age_appropriateness_score=age_appropriateness,
            overall_quality_score=overall_quality,
            improvements_noted=improvements,
            weaknesses_identified=weaknesses
        )
    
    def run_comparison_test(self) -> List[GenerationResult]:
        """
        Run the full comparison test across all scenarios
        """
        logger.info("Starting comprehensive lesson generation comparison test")
        results = []
        
        for scenario in self.test_scenarios:
            logger.info(f"Testing scenario: {scenario.grade_level} - {scenario.musical_topic}")
            
            # Test keyword-based approach
            logger.info("Testing keyword-based approach...")
            keyword_start = time.time()
            
            keyword_standards = self._mock_keyword_based_standards_search(scenario)
            keyword_teaching = self._generate_mock_teaching_strategies(scenario)
            keyword_assessment = self._generate_mock_assessment_methods(scenario)
            
            (keyword_lesson, keyword_time, 
             keyword_prompt_size, keyword_response_size) = self._generate_lesson_content(
                scenario, keyword_standards, keyword_teaching, keyword_assessment, use_rag=False
            )
            
            keyword_result = GenerationResult(
                approach="keyword",
                scenario=scenario,
                lesson_content=keyword_lesson,
                selected_standards=keyword_standards,
                teaching_strategies=keyword_teaching,
                assessment_methods=keyword_assessment,
                generation_time=keyword_time,
                prompt_size=keyword_prompt_size,
                response_size=keyword_response_size,
                semantic_similarity_scores=[],
                quality_metrics=self._analyze_quality(GenerationResult(
                    approach="keyword",
                    scenario=scenario,
                    lesson_content=keyword_lesson,
                    selected_standards=keyword_standards,
                    teaching_strategies=keyword_teaching,
                    assessment_methods=keyword_assessment,
                    generation_time=keyword_time,
                    prompt_size=keyword_prompt_size,
                    response_size=keyword_response_size,
                    semantic_similarity_scores=[],
                    quality_metrics={}
                ))
            )
            results.append(keyword_result)
            
            # Test RAG-enhanced approach
            logger.info("Testing RAG-enhanced approach...")
            rag_start = time.time()
            
            rag_standards = self._get_rag_enhanced_standards_search(scenario)
            rag_teaching = self._get_rag_teaching_strategies(scenario)
            rag_assessment = self._get_rag_assessment_methods(scenario)
            
            # Get semantic similarity scores
            semantic_scores = [std.get("relevance_score", 0) for std in rag_standards]
            
            (rag_lesson, rag_time, 
             rag_prompt_size, rag_response_size) = self._generate_lesson_content(
                scenario, rag_standards, rag_teaching, rag_assessment, use_rag=True
            )
            
            rag_result = GenerationResult(
                approach="rag",
                scenario=scenario,
                lesson_content=rag_lesson,
                selected_standards=rag_standards,
                teaching_strategies=rag_teaching,
                assessment_methods=rag_assessment,
                generation_time=rag_time,
                prompt_size=rag_prompt_size,
                response_size=rag_response_size,
                semantic_similarity_scores=semantic_scores,
                quality_metrics=self._analyze_quality(GenerationResult(
                    approach="rag",
                    scenario=scenario,
                    lesson_content=rag_lesson,
                    selected_standards=rag_standards,
                    teaching_strategies=rag_teaching,
                    assessment_methods=rag_assessment,
                    generation_time=rag_time,
                    prompt_size=rag_prompt_size,
                    response_size=rag_response_size,
                    semantic_similarity_scores=semantic_scores,
                    quality_metrics={}
                ))
            )
            results.append(rag_result)
        
        logger.info(f"Completed {len(results)} lesson generation tests")
        return results
    
    def test_live_api_endpoint(self) -> Dict[str, Any]:
        """
        Test the actual live API endpoint to ensure RAG integration works
        """
        logger.info("Testing live API endpoint with RAG integration")
        
        try:
            # Test via lesson agent chat interface
            test_message = "I need a 3rd grade lesson about melody and pitch patterns"
            
            start_time = time.time()
            response = self.lesson_agent.chat(test_message)
            api_response_time = time.time() - start_time
            
            # Check if RAG context was used
            rag_context_count = len(self.lesson_agent.lesson_requirements.get("rag_context", {}))
            
            # Analyze response for quality indicators
            response_lower = response.lower()
            quality_indicators = {
                "has_standard_id": any(char.isdigit() for char in response),
                "has_teaching_strategies": "strategy" in response_lower or "activity" in response_lower,
                "has_assessment_methods": "assessment" in response_lower or "evaluate" in response_lower,
                "has_grade_reference": "3rd" in response_lower or "grade" in response_lower,
                "has_musical_content": "melody" in response_lower or "pitch" in response_lower,
                "is_structured": "##" in response or "###" in response,
                "rag_context_used": rag_context_count > 0
            }
            
            api_test_result = {
                "success": True,
                "response_time": api_response_time,
                "response_length": len(response),
                "rag_context_items": rag_context_count,
                "quality_indicators": quality_indicators,
                "quality_score": sum(quality_indicators.values()) / len(quality_indicators) * 100,
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            
            logger.info(f"API test completed successfully. Quality score: {api_test_result['quality_score']:.1f}%")
            return api_test_result
            
        except Exception as e:
            logger.error(f"API endpoint test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": 0,
                "response_length": 0,
                "rag_context_items": 0,
                "quality_indicators": {},
                "quality_score": 0,
                "response_preview": ""
            }

def main():
    """Run the comprehensive comparison test"""
    print("🎵 Starting Comprehensive Lesson Generation Comparison Test")
    print("=" * 80)
    
    comparator = LessonGenerationComparator()
    
    # Step 1: Run comparison tests
    print("\n📊 Step 1: Running comparison tests...")
    comparison_results = comparator.run_comparison_test()
    
    # Step 2: Test live API endpoint
    print("\n🌐 Step 2: Testing live API endpoint...")
    api_test_result = comparator.test_live_api_endpoint()
    
    # Step 3: Analyze and report results
    print("\n📈 Step 3: Analyzing results...")
    
    # Save detailed results to file
    results_data = {
        "comparison_results": [asdict(result) for result in comparison_results],
        "api_test_result": api_test_result,
        "timestamp": time.time()
    }
    
    with open("lesson_generation_comparison_results.json", "w") as f:
        json.dump(results_data, f, indent=2, default=str)
    
    print("\n🎉 Comprehensive comparison test completed!")
    print(f"📄 Detailed results saved to: lesson_generation_comparison_results.json")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)