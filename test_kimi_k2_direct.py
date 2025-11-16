"""Direct test of Kimi K2 Thinking model for lesson generation"""

import json
from datetime import datetime
from pathlib import Path

from backend.llm.chutes_client import ChutesClient, Message
from backend.repositories.standards_repository import StandardsRepository
from backend.llm.prompt_templates import LessonPromptContext


def test_kimi_k2_direct():
    """Test Kimi K2 model directly with a sample lesson"""

    print("\n" + "=" * 80)
    print("DIRECT KIMI K2 THINKING MODEL TEST")
    print("=" * 80)

    # Initialize client with explicit Kimi K2 model
    client = ChutesClient(default_model="moonshotai/Kimi-K2-Thinking")

    print(f"\nModel: {client.default_model}")
    print(f"API Available: {client.is_available()}")

    # Get a real standard from the database
    standards_repo = StandardsRepository()

    # Get available grade levels
    grade_levels = standards_repo.get_grade_levels()
    print(f"\nAvailable grade levels: {grade_levels[:5]}")

    # Use first available grade level with standards
    standards = []
    for grade in grade_levels:
        standards = standards_repo.get_standards_by_grade(grade)
        if standards:
            print(f"Using grade level: {grade}")
            break

    if not standards:
        print("ERROR: No standards found!")
        return

    # Use first standard
    standard = standards[0]
    objectives = standards_repo.get_objectives_for_standard(standard.standard_id)

    print(f"\nUsing Standard: {standard.standard_id}")
    print(f"Standard Text: {standard.standard_text[:100]}...")
    print(f"Objectives: {len(objectives)} found")

    # Create lesson context
    grade_level = grade_levels[0] if grade_levels else "Third Grade"
    context = LessonPromptContext(
        grade_level=grade_level,
        strand_code=standard.strand_code,
        strand_name=standard.strand_name,
        strand_description=standard.strand_description,
        standard_id=standard.standard_id,
        standard_text=standard.standard_text,
        objectives=[
            f"{obj.objective_id} - {obj.objective_text}" for obj in objectives[:3]
        ],
        additional_context="Focus on rhythmic patterns using body percussion",
        lesson_duration="45 minutes",
        class_size=25,
        available_resources=["body percussion", "rhythm sticks", "drums"],
    )

    print("\n" + "-" * 80)
    print("GENERATING LESSON WITH KIMI K2...")
    print("-" * 80)

    # Generate lesson
    start_time = datetime.now()
    lesson_plan = client.generate_lesson_plan(context, stream=False)
    end_time = datetime.now()

    generation_time = (end_time - start_time).total_seconds()

    # Handle Union[str, Iterator[str]] return type
    if isinstance(lesson_plan, str):
        final_plan = lesson_plan
    else:
        final_plan = "".join(lesson_plan)

    print(f"\n✓ Generation completed in {generation_time:.1f} seconds")
    print(
        f"✓ Lesson length: {len(final_plan)} characters ({len(final_plan.split())} words)"
    )

    # Print first part of lesson
    print("\n" + "=" * 80)
    print("LESSON PLAN PREVIEW (First 1000 characters)")
    print("=" * 80)
    print(final_plan[:1000])
    print("...")

    # Quality analysis
    print("\n" + "=" * 80)
    print("QUALITY ANALYSIS")
    print("=" * 80)

    metrics = {
        "Has objectives": "objective" in final_plan.lower()
        or "goal" in final_plan.lower(),
        "Has activities": "activity" in final_plan.lower()
        or "procedure" in final_plan.lower(),
        "Has assessment": "assessment" in final_plan.lower()
        or "evaluation" in final_plan.lower(),
        "Has materials": "material" in final_plan.lower()
        or "resource" in final_plan.lower(),
        "Has standards reference": standard.standard_id in final_plan,
        "Has timing information": "minute" in final_plan.lower()
        or "time" in final_plan.lower(),
        "Adequate length (>1000 chars)": len(final_plan) > 1000,
        "Well structured (markdown)": final_plan.count("#") > 3,
        "Has differentiation": "differentiat" in final_plan.lower()
        or "scaffold" in final_plan.lower(),
        "Has extensions": "extension" in final_plan.lower()
        or "enrich" in final_plan.lower(),
    }

    for metric, passed in metrics.items():
        status = "✓" if passed else "✗"
        print(f"{status} {metric}")

    quality_score = sum(metrics.values()) / len(metrics) * 100
    print(f"\nOverall Quality Score: {quality_score:.1f}%")

    # Save full lesson
    output_dir = Path("archive/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"kimi_k2_direct_test_{timestamp}.json"

    output_data = {
        "model": "moonshotai/Kimi-K2-Thinking",
        "timestamp": datetime.now().isoformat(),
        "generation_time_seconds": generation_time,
        "standard": {
            "standard_id": standard.standard_id,
            "grade_level": "Third Grade",
            "strand": standard.strand_name,
        },
        "lesson_plan": final_plan,
        "quality_metrics": metrics,
        "quality_score": quality_score,
        "lesson_stats": {
            "characters": len(final_plan),
            "words": len(final_plan.split()),
            "lines": len(final_plan.split("\n")),
        },
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n\nFull lesson saved to: {output_file}")

    # Print conclusion
    print("\n" + "=" * 80)
    if quality_score >= 80:
        print("✅ EXCELLENT: Kimi K2 produces high-quality lesson plans!")
    elif quality_score >= 70:
        print("✓ GOOD: Kimi K2 produces acceptable lesson plans")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Quality below threshold")
    print("=" * 80 + "\n")

    return output_data


def compare_models():
    """Compare Kimi K2 vs Qwen3-VL on the same prompt"""

    print("\n" + "=" * 80)
    print("MODEL COMPARISON: Kimi K2 vs Qwen3-VL")
    print("=" * 80)

    # Get a standard
    standards_repo = StandardsRepository()
    grade_levels = standards_repo.get_grade_levels()

    # Find a grade with standards
    standards = []
    grade_level = "Fifth Grade"
    for grade in grade_levels:
        standards = standards_repo.get_standards_by_grade(grade)
        if standards:
            grade_level = grade
            break

    if not standards:
        print("ERROR: No standards found in database!")
        return {}

    standard = standards[0]
    objectives = standards_repo.get_objectives_for_standard(standard.standard_id)

    # Create lesson context
    context = LessonPromptContext(
        grade_level=grade_level,
        strand_code=standard.strand_code,
        strand_name=standard.strand_name,
        strand_description=standard.strand_description,
        standard_id=standard.standard_id,
        standard_text=standard.standard_text,
        objectives=[
            f"{obj.objective_id} - {obj.objective_text}" for obj in objectives[:2]
        ],
        additional_context="Students will explore melodic composition using xylophones",
        lesson_duration="45 minutes",
        class_size=25,
        available_resources=[
            "xylophones",
            "notation paper",
            "tablets with music notation apps",
        ],
    )

    results = {}

    # Test both models
    for model_name in [
        "moonshotai/Kimi-K2-Thinking",
        "Qwen/Qwen3-VL-235B-A22B-Instruct",
    ]:
        print(f"\n{'-' * 80}")
        print(f"Testing: {model_name}")
        print(f"{'-' * 80}")

        client = ChutesClient(default_model=model_name)

        start_time = datetime.now()
        lesson_plan = client.generate_lesson_plan(context, stream=False)
        end_time = datetime.now()

        # Handle Union[str, Iterator[str]]
        if isinstance(lesson_plan, str):
            final_plan = lesson_plan
        else:
            final_plan = "".join(lesson_plan)

        generation_time = (end_time - start_time).total_seconds()

        # Analyze
        metrics = {
            "objectives": "objective" in final_plan.lower(),
            "activities": "activity" in final_plan.lower(),
            "assessment": "assessment" in final_plan.lower(),
            "materials": "material" in final_plan.lower(),
            "timing": "minute" in final_plan.lower(),
            "differentiation": "differentiat" in final_plan.lower(),
            "standards": standard.standard_id in final_plan,
            "structured": final_plan.count("#") > 3,
        }

        quality_score = sum(metrics.values()) / len(metrics) * 100

        results[model_name] = {
            "generation_time": generation_time,
            "length": len(final_plan),
            "words": len(final_plan.split()),
            "quality_score": quality_score,
            "metrics": metrics,
            "preview": final_plan[:500],
        }

        print(f"✓ Time: {generation_time:.1f}s")
        print(f"✓ Length: {len(final_plan)} chars ({len(final_plan.split())} words)")
        print(f"✓ Quality Score: {quality_score:.1f}%")

    # Print comparison
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)

    kimi_score = results["moonshotai/Kimi-K2-Thinking"]["quality_score"]
    qwen_score = results["Qwen/Qwen3-VL-235B-A22B-Instruct"]["quality_score"]

    print(f"\nKimi K2 Quality Score: {kimi_score:.1f}%")
    print(f"Qwen3-VL Quality Score: {qwen_score:.1f}%")

    if kimi_score > qwen_score:
        print(f"\n✅ Kimi K2 wins by {kimi_score - qwen_score:.1f} points!")
    elif qwen_score > kimi_score:
        print(f"\n✅ Qwen3-VL wins by {qwen_score - kimi_score:.1f} points!")
    else:
        print(f"\n🤝 Tie! Both models score {kimi_score:.1f}%")

    # Save comparison
    output_dir = Path("archive/reports")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"model_comparison_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nComparison saved to: {output_file}\n")

    return results


if __name__ == "__main__":
    # Run direct test
    print("\n🔬 Running Kimi K2 Direct Test...\n")
    test_kimi_k2_direct()

    # Run comparison
    print("\n🔬 Running Model Comparison...\n")
    compare_models()
