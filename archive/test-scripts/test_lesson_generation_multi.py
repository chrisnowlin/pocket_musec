#!/usr/bin/env python3
"""Test multiple lesson generation scenarios"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_lesson_scenario(grade_choice, strand_choice, standard_choice, description):
    """Test a specific lesson generation scenario"""

    console.print(f"\n[bold cyan]Testing: {description}[/bold cyan]")
    console.print("-" * 40)

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

        # Quick conversation flow
        agent.chat("")  # Welcome
        agent.chat(str(grade_choice))  # Grade
        agent.chat(str(strand_choice))  # Strand
        agent.chat(str(standard_choice))  # Standard
        agent.chat("1")  # First objective
        agent.chat("skip")  # Skip additional context

        # Check result
        if agent.get_state() == "complete":
            lesson = agent.get_generated_lesson()
            requirements = agent.get_lesson_requirements()

            console.print(f"✅ [green]Success[/green]")
            console.print(f"  Grade: {requirements.get('grade_level')}")
            console.print(f"  Strand: {requirements.get('strand_code')}")
            console.print(f"  Standard: {requirements.get('standard_id')}")
            console.print(f"  Lesson length: {len(lesson) if lesson else 0} chars")

            return True
        else:
            console.print(f"❌ [red]Failed at state: {agent.get_state()}[/red]")
            return False

    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        return False


def main():
    """Run multiple lesson generation scenarios"""

    console.print(
        Panel.fit(
            "[bold blue]Multi-Scenario Lesson Generation Test[/bold blue]\n"
            "Testing different grade levels and standards",
            border_style="blue",
        )
    )

    # Test scenarios
    scenarios = [
        (1, 1, 1, "Grade 1 - Connect - 1.CN.1"),
        (3, 2, 1, "Grade 3 - Create - 3.CR.1"),
        (5, 3, 1, "Grade 5 - Present - 5.PR.1"),
    ]

    results = []
    for grade, strand, standard, desc in scenarios:
        success = test_lesson_scenario(grade, strand, standard, desc)
        results.append((desc, success))

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Summary[/bold]")
    console.print("=" * 60)

    passed = 0
    for desc, success in results:
        status = "[green]✅ PASSED[/green]" if success else "[red]❌ FAILED[/red]"
        console.print(f"{desc[:30]:.<40} {status}")
        if success:
            passed += 1

    console.print("=" * 60)
    console.print(f"[bold]Overall: {passed}/{len(results)} scenarios passed[/bold]")

    if passed == len(results):
        console.print("\n[bold green]🎉 All scenarios successful![/bold green]")
        return 0
    else:
        console.print(
            f"\n[bold yellow]⚠️  {len(results) - passed} scenario(s) failed[/bold yellow]"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
