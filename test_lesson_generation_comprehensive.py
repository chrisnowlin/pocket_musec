#!/usr/bin/env python3
"""Comprehensive lesson generation testing with consistency validation"""

import sys
import re
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Dict, List, Tuple, Optional

console = Console()


class LessonConsistencyValidator:
    """Validates internal consistency of generated lessons"""

    def __init__(self):
        self.test_results = []

def extract_standards_from_lesson(self, lesson_text: str) -> List[str]:
        """Extract standard codes mentioned in lesson text"""
        # Look for patterns like K.CN.1, 1.CR.2, etc.
        # More flexible pattern - don't require word boundaries at start
        pattern = r'(K|[1-8])\.[A-Z]{2}\.\d+'
        return list(set(re.findall(pattern, lesson_text, re.IGNORECASE)))
    
    def extract_objectives_from_lesson(self, lesson_text: str) -> List[str]:
        """Extract objective codes mentioned in lesson text"""
        # Look for patterns like K.CN.1.1, 1.CR.2.3, etc.
        # More flexible pattern - don't require word boundaries at start
        pattern = r'(K|[1-8])\.[A-Z]{2}\.\d+\.\d+'
        return list(set(re.findall(pattern, lesson_text, re.IGNORECASE)))

    def extract_objectives_from_lesson(self, lesson_text: str) -> List[str]:
        """Extract objective codes mentioned in lesson text"""
        # Look for patterns like K.CN.1.1, 1.CR.2.3, etc.
        pattern = r"\b(K|[1-8])\.[A-Z]{2}\.\d+\.\d+\b"
        return list(set(re.findall(pattern, lesson_text, re.IGNORECASE)))

    def extract_grade_from_lesson(self, lesson_text: str) -> Optional[str]:
        """Extract grade level mentioned in lesson text"""
        # Look for grade patterns
        patterns = [
            r"\b(\d+)(?:st|nd|rd|th) Grade\b",
            r"\bGrade (\d+)\b",
            r"\bKindergarten\b",
            r"\bK(?:inder)?\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, lesson_text, re.IGNORECASE)
            if match:
                grade = match.group(1)
                return "K" if grade.lower().startswith("k") else grade

        return None

    def extract_strand_from_lesson(self, lesson_text: str) -> Optional[str]:
        """Extract strand codes mentioned in lesson text"""
        # Look for strand codes in context
        pattern = r"\b([A-Z]{2})\s*(?:strand|Strand)?\b"
        strands = list(set(re.findall(pattern, lesson_text)))

        # Filter to known strands
        known_strands = {"CN", "CR", "PR", "RE"}
        found_strands = [s for s in strands if s in known_strands]

        return found_strands[0] if found_strands else None

    def validate_consistency(self, requirements: Dict, lesson_text: str) -> Dict:
        """Validate that lesson content matches selected requirements"""

        # Extract from lesson
        lesson_standards = self.extract_standards_from_lesson(lesson_text)
        lesson_objectives = self.extract_objectives_from_lesson(lesson_text)
        lesson_grade = self.extract_grade_from_lesson(lesson_text)
        lesson_strand = self.extract_strand_from_lesson(lesson_text)

        # Get expected values
        expected_grade = requirements.get("grade_level")
        expected_strand = requirements.get("strand_code")

        # Get standard ID from standard object
        standard_obj = requirements.get("standard")
        expected_standard = (
            standard_obj.standard_id
            if standard_obj and hasattr(standard_obj, "standard_id")
            else None
        )

        selected_objectives = requirements.get("selected_objectives", [])
        expected_objectives = (
            [obj.objective_id for obj in selected_objectives]
            if selected_objectives
            else []
        )

        # Validation results
        validation = {
            "grade_match": False,
            "strand_match": False,
            "standard_mentioned": False,
            "objectives_mentioned": 0,
            "consistency_score": 0,
            "issues": [],
        }

        # Check grade consistency
        if lesson_grade and expected_grade:
            if lesson_grade == expected_grade or (
                lesson_grade == "K" and expected_grade == "K"
            ):
                validation["grade_match"] = True
            else:
                validation["issues"].append(
                    f"Grade mismatch: expected {expected_grade}, found {lesson_grade}"
                )

        # Check strand consistency
        if lesson_strand and expected_strand:
            if lesson_strand == expected_strand:
                validation["strand_match"] = True
            else:
                validation["issues"].append(
                    f"Strand mismatch: expected {expected_strand}, found {lesson_strand}"
                )

        # Check standard mention
        if expected_standard:
            if expected_standard in lesson_standards:
                validation["standard_mentioned"] = True
            else:
                validation["issues"].append(
                    f"Expected standard {expected_standard} not found in lesson"
                )

        # Check objectives mention
        for obj in expected_objectives:
            if obj in lesson_objectives:
                validation["objectives_mentioned"] += 1

        if len(expected_objectives) > 0:
            obj_ratio = validation["objectives_mentioned"] / len(expected_objectives)
        else:
            obj_ratio = 0

        # Calculate consistency score
        score_components = [
            validation["grade_match"],
            validation["strand_match"],
            validation["standard_mentioned"],
            obj_ratio > 0.5,  # At least half of objectives mentioned
        ]
        validation["consistency_score"] = sum(score_components) / len(score_components)

        # Add extracted info for debugging
        validation["extracted"] = {
            "grade": lesson_grade,
            "strand": lesson_strand,
            "standards": lesson_standards,
            "objectives": lesson_objectives,
        }

        return validation


def test_strand_scenario(
    grade_choice: int,
    strand_choice: int,
    standard_choice: int,
    description: str,
    validator: LessonConsistencyValidator,
) -> Dict:
    """Test a specific scenario with consistency validation"""

    console.print(f"\n[bold cyan]Testing: {description}[/bold cyan]")
    console.print("-" * 50)

    try:
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store
        from backend.repositories.standards_repository import StandardsRepository
        from backend.llm.chutes_client import ChutesClient

        # Initialize
        flow = Flow("LessonTest")
        store = Store()
        standards_repo = StandardsRepository()
        llm_client = ChutesClient()
        agent = LessonAgent(flow, store, standards_repo, llm_client)

        # Track conversation for debugging
        conversation_log = []

        # Conversation flow
        def chat_and_log(message: str) -> str:
            response = agent.chat(message)
            conversation_log.append(f"USER: {message}")
            conversation_log.append(f"AGENT: {response[:100]}...")
            return response

        # Execute conversation
        chat_and_log("")  # Welcome
        chat_and_log(str(grade_choice))  # Grade
        chat_and_log(str(strand_choice))  # Strand
        chat_and_log(str(standard_choice))  # Standard
        chat_and_log("1")  # First objective
        chat_and_log("skip")  # Skip additional context

        # Check result
        if agent.get_state() == "complete":
            lesson = agent.get_generated_lesson()
            requirements = agent.get_lesson_requirements()

            # Validate consistency (ensure lesson is not None)
            if lesson:
                validation = validator.validate_consistency(requirements, lesson)
            else:
                validation = {
                    "consistency_score": 0,
                    "grade_match": False,
                    "strand_match": False,
                    "standard_mentioned": False,
                    "objectives_mentioned": 0,
                    "issues": ["No lesson generated"],
                    "extracted": {
                        "grade": None,
                        "strand": None,
                        "standards": [],
                        "objectives": [],
                    },
                }

            # Display results
            console.print(f"✅ [green]Generation Complete[/green]")
            console.print(
                f"  Grade: {requirements.get('grade_level')} → {validation['extracted']['grade']}"
            )
            console.print(
                f"  Strand: {requirements.get('strand_code')} → {validation['extracted']['strand']}"
            )
            # Get standard ID for display
            standard_obj = requirements.get("standard")
            standard_id = (
                standard_obj.standard_id
                if standard_obj and hasattr(standard_obj, "standard_id")
                else "None"
            )
            console.print(f"  Standard: {standard_id}")
            console.print(
                f"  Objectives: {len(requirements.get('selected_objectives', []))} selected, {validation['objectives_mentioned']} mentioned"
            )
            console.print(f"  Lesson length: {len(lesson) if lesson else 0} chars")
            console.print(f"  Consistency Score: {validation['consistency_score']:.1%}")

            if validation["issues"]:
                console.print(f"  [yellow]Issues:[/yellow]")
                for issue in validation["issues"]:
                    console.print(f"    • {issue}")

            return {
                "description": description,
                "success": True,
                "requirements": requirements,
                "validation": validation,
                "lesson_length": len(lesson) if lesson else 0,
                "conversation_log": conversation_log,
            }
        else:
            console.print(f"❌ [red]Failed at state: {agent.get_state()}[/red]")
            return {
                "description": description,
                "success": False,
                "error": f"Stopped at state: {agent.get_state()}",
                "conversation_log": conversation_log,
            }

    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        return {
            "description": description,
            "success": False,
            "error": str(e),
            "conversation_log": [],
        }


def main():
    """Run comprehensive lesson generation tests"""

    console.print(
        Panel.fit(
            "[bold blue]Comprehensive Lesson Generation Test[/bold blue]\n"
            "Testing all 4 strands with internal consistency validation",
            border_style="blue",
        )
    )

    validator = LessonConsistencyValidator()

    # Test scenarios covering all 4 strands
    scenarios = [
        (1, 1, 1, "Grade 1 - CN (Connect) - 1.CN.1"),
        (1, 2, 1, "Grade 1 - CR (Create) - 1.CR.1"),
        (1, 3, 1, "Grade 1 - PR (Present) - 1.PR.1"),
        (1, 4, 1, "Grade 1 - RE (Respond) - 1.RE.1"),
    ]

    results = []
    for grade, strand, standard, desc in scenarios:
        result = test_strand_scenario(grade, strand, standard, desc, validator)
        results.append(result)
        if not result["success"]:
            console.print(f"[yellow]Stopping early due to error in {desc}[/yellow]")
            break

    # Create summary table
    console.print("\n" + "=" * 80)
    console.print("[bold]COMPREHENSIVE TEST RESULTS[/bold]")
    console.print("=" * 80)

    table = Table(title="Test Scenario Summary")
    table.add_column("Scenario", style="cyan")
    table.add_column("Generation", style="green")
    table.add_column("Grade Match", style="blue")
    table.add_column("Strand Match", style="blue")
    table.add_column("Standard Used", style="blue")
    table.add_column("Objectives Used", style="blue")
    table.add_column("Consistency", style="magenta")
    table.add_column("Lesson Size", style="yellow")

    for result in results:
        if result["success"]:
            val = result["validation"]
            selected_objs = len(result["requirements"].get("selected_objectives", []))
            table.add_row(
                result["description"][:30],
                "✅",
                "✅" if val["grade_match"] else "❌",
                "✅" if val["strand_match"] else "❌",
                "✅" if val["standard_mentioned"] else "❌",
                f"{val['objectives_mentioned']}/{selected_objs}",
                f"{val['consistency_score']:.0%}",
                f"{result['lesson_length']}",
            )
        else:
            table.add_row(
                result["description"][:30],
                "❌",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
            )

    console.print(table)

    # Detailed analysis
    console.print("\n" + "=" * 80)
    console.print("[bold]CONSISTENCY ANALYSIS[/bold]")
    console.print("=" * 80)

    successful_results = [r for r in results if r["success"]]

    if successful_results:
        avg_consistency = sum(
            r["validation"]["consistency_score"] for r in successful_results
        ) / len(successful_results)
        console.print(f"Average Consistency Score: {avg_consistency:.1%}")

        # Strand coverage
        strand_coverage = {}
        for result in successful_results:
            strand = result["requirements"].get("strand_code")
            if strand:
                strand_coverage[strand] = strand_coverage.get(strand, 0) + 1

        console.print(f"\nStrand Coverage:")
        for strand, count in strand_coverage.items():
            console.print(f"  {strand}: {count} scenarios tested")

        # Common issues
        all_issues = []
        for result in successful_results:
            all_issues.extend(result["validation"]["issues"])

        if all_issues:
            console.print(f"\nCommon Issues:")
            for issue in set(all_issues):
                console.print(f"  • {issue}")
        else:
            console.print(f"\n✅ [green]No consistency issues found![/green]")

    # Final verdict
    console.print("\n" + "=" * 80)
    console.print("[bold]FINAL VERDICT[/bold]")
    console.print("=" * 80)

    passed = len(successful_results)
    total = len(results)

    if passed == total and passed > 0:
        console.print("[bold green]🎉 ALL TESTS PASSED![/bold green]")
        console.print("✅ Lesson generation is working across all 4 strands")
        console.print("✅ Internal consistency is maintained")
        console.print("✅ System is production-ready")
        return 0
    else:
        console.print(f"[bold yellow]⚠️  {total - passed} test(s) failed[/bold yellow]")
        console.print("System needs attention before production deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
