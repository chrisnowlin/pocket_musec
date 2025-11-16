"""Test script for Kimi K2 Thinking model lesson generation quality"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from backend.llm.chutes_client import ChutesClient
from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.config import config


def test_scenario_1_rhythm_elementary():
    """Test 1: Elementary rhythm lesson"""
    print("\n" + "=" * 80)
    print("TEST 1: Elementary Rhythm Lesson (3rd Grade)")
    print("=" * 80)

    # Initialize components
    standards_repo = StandardsRepository()
    llm_client = ChutesClient()
    flow = Flow()
    store = Store()

    # Create agent in conversational mode
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standards_repo,
        llm_client=llm_client,
        conversational_mode=True,
    )

    # Simulate conversation
    messages = ["I need a rhythm lesson for 3rd graders", "generate lesson plan"]

    responses = []
    for msg in messages:
        print(f"\nUser: {msg}")
        response = agent.chat(msg)
        print(f"\nAssistant: {response[:500]}...")  # First 500 chars
        responses.append(response)

    # Extract the final lesson plan
    lesson_plan = responses[-1]

    return {
        "test_name": "Elementary Rhythm (3rd Grade)",
        "model": config.llm.default_model,
        "lesson_plan": lesson_plan,
        "timestamp": datetime.now().isoformat(),
    }


def test_scenario_2_melody_middle_school():
    """Test 2: Middle school melody composition"""
    print("\n" + "=" * 80)
    print("TEST 2: Middle School Melody Composition (Grade 7)")
    print("=" * 80)

    # Initialize components
    standards_repo = StandardsRepository()
    llm_client = ChutesClient()
    flow = Flow()
    store = Store()

    # Create agent in conversational mode
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standards_repo,
        llm_client=llm_client,
        conversational_mode=True,
    )

    # Simulate conversation
    messages = [
        "I want to teach melody composition to my 7th grade students. We have keyboards and notation software available.",
        "generate lesson plan",
    ]

    responses = []
    for msg in messages:
        print(f"\nUser: {msg}")
        response = agent.chat(msg)
        print(f"\nAssistant: {response[:500]}...")  # First 500 chars
        responses.append(response)

    # Extract the final lesson plan
    lesson_plan = responses[-1]

    return {
        "test_name": "Middle School Melody Composition (Grade 7)",
        "model": config.llm.default_model,
        "lesson_plan": lesson_plan,
        "timestamp": datetime.now().isoformat(),
    }


def test_scenario_3_singing_primary():
    """Test 3: Primary singing lesson"""
    print("\n" + "=" * 80)
    print("TEST 3: Primary Singing Lesson (Kindergarten)")
    print("=" * 80)

    # Initialize components
    standards_repo = StandardsRepository()
    llm_client = ChutesClient()
    flow = Flow()
    store = Store()

    # Create agent in conversational mode
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standards_repo,
        llm_client=llm_client,
        conversational_mode=True,
    )

    # Simulate conversation
    messages = [
        "I need a fun singing lesson for kindergarten students focusing on pitch exploration",
        "generate lesson plan",
    ]

    responses = []
    for msg in messages:
        print(f"\nUser: {msg}")
        response = agent.chat(msg)
        print(f"\nAssistant: {response[:500]}...")  # First 500 chars
        responses.append(response)

    # Extract the final lesson plan
    lesson_plan = responses[-1]

    return {
        "test_name": "Primary Singing (Kindergarten)",
        "model": config.llm.default_model,
        "lesson_plan": lesson_plan,
        "timestamp": datetime.now().isoformat(),
    }


def analyze_lesson_quality(result):
    """Analyze the quality of a generated lesson plan"""
    lesson = result["lesson_plan"]

    # Quality metrics
    metrics = {
        "has_objectives": "objective" in lesson.lower() or "goal" in lesson.lower(),
        "has_activities": "activity" in lesson.lower() or "procedure" in lesson.lower(),
        "has_assessment": "assessment" in lesson.lower()
        or "evaluation" in lesson.lower(),
        "has_materials": "material" in lesson.lower() or "resource" in lesson.lower(),
        "has_standards": any(
            code in lesson for code in ["MU:", "CN:", "RE:", "PR:", "CR:"]
        ),
        "has_timing": "minute" in lesson.lower() or "time" in lesson.lower(),
        "length_adequate": len(lesson) > 1000,  # At least 1000 chars
        "well_structured": lesson.count("#") > 3,  # Has markdown headers
    }

    score = sum(metrics.values()) / len(metrics) * 100

    return {
        "quality_score": score,
        "metrics": metrics,
        "lesson_length": len(lesson),
        "word_count": len(lesson.split()),
    }


def save_results(results, quality_analyses):
    """Save test results to file"""
    output_dir = Path("archive/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"kimi_k2_lesson_quality_test_{timestamp}.json"

    output_data = {
        "test_metadata": {
            "model": config.llm.default_model,
            "timestamp": datetime.now().isoformat(),
            "test_count": len(results),
        },
        "results": [
            {**result, "quality_analysis": quality_analyses[i]}
            for i, result in enumerate(results)
        ],
        "summary": {
            "average_quality_score": sum(qa["quality_score"] for qa in quality_analyses)
            / len(quality_analyses),
            "all_tests_passed": all(
                qa["quality_score"] >= 70 for qa in quality_analyses
            ),
        },
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")
    return output_file


def print_summary(quality_analyses):
    """Print quality summary"""
    print("\n" + "=" * 80)
    print("QUALITY SUMMARY")
    print("=" * 80)

    for i, qa in enumerate(quality_analyses, 1):
        print(f"\nTest {i} Quality Score: {qa['quality_score']:.1f}%")
        print(
            f"  - Lesson Length: {qa['lesson_length']} chars ({qa['word_count']} words)"
        )
        print(f"  - Metrics:")
        for metric, value in qa["metrics"].items():
            status = "✓" if value else "✗"
            print(f"    {status} {metric.replace('_', ' ').title()}")

    avg_score = sum(qa["quality_score"] for qa in quality_analyses) / len(
        quality_analyses
    )
    print(f"\n{'=' * 80}")
    print(f"AVERAGE QUALITY SCORE: {avg_score:.1f}%")
    print(f"{'=' * 80}")

    if avg_score >= 80:
        print("\n✅ EXCELLENT: Kimi K2 lessons meet high quality standards!")
    elif avg_score >= 70:
        print("\n✓ GOOD: Kimi K2 lessons meet acceptable quality standards")
    else:
        print("\n⚠️  NEEDS IMPROVEMENT: Quality below acceptable threshold")


def main():
    """Run all test scenarios"""
    print("\n" + "=" * 80)
    print("KIMI K2 THINKING MODEL - LESSON GENERATION QUALITY TEST")
    print("=" * 80)
    print(f"Default Model: {config.llm.default_model}")
    print(f"Test Start: {datetime.now().isoformat()}")

    # Run test scenarios
    results = []

    try:
        # Test 1
        result1 = test_scenario_1_rhythm_elementary()
        results.append(result1)
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")

    try:
        # Test 2
        result2 = test_scenario_2_melody_middle_school()
        results.append(result2)
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")

    try:
        # Test 3
        result3 = test_scenario_3_singing_primary()
        results.append(result3)
    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")

    # Analyze quality
    quality_analyses = [analyze_lesson_quality(result) for result in results]

    # Print summary
    print_summary(quality_analyses)

    # Save results
    output_file = save_results(results, quality_analyses)

    print(f"\n\n{'=' * 80}")
    print("TEST COMPLETE")
    print(f"{'=' * 80}\n")

    return results, quality_analyses


if __name__ == "__main__":
    main()
