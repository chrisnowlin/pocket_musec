#!/usr/bin/env python3
"""Debug lesson requirements to understand consistency issues"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json

console = Console()


def debug_lesson_requirements():
    """Debug what's actually stored in lesson requirements"""

    console.print(
        Panel.fit(
            "[bold blue]Debugging Lesson Requirements[/bold blue]\n"
            "Investigating consistency issues with standards and objectives",
            border_style="blue",
        )
    )

    try:
        from backend.pocketflow.lesson_agent import LessonAgent
        from backend.pocketflow.flow import Flow
        from backend.pocketflow.store import Store
        from backend.repositories.standards_repository import StandardsRepository
        from backend.llm.chutes_client import ChutesClient

        # Initialize
        flow = Flow("DebugTest")
        store = Store()
        standards_repo = StandardsRepository()
        llm_client = ChutesClient()
        agent = LessonAgent(flow, store, standards_repo, llm_client)

        console.print("✅ Agent initialized")

        # Execute conversation
        console.print("\n🤖 Executing conversation...")
        agent.chat("")  # Welcome
        agent.chat("1")  # Grade 1
        agent.chat("1")  # CN strand
        agent.chat("1")  # First standard
        agent.chat("1")  # First objective
        agent.chat("skip")  # Skip context

        if agent.get_state() == "complete":
            requirements = agent.get_lesson_requirements()
            lesson = agent.get_generated_lesson()

            console.print("\n[bold cyan]REQUIREMENTS ANALYSIS[/bold cyan]")
            console.print("=" * 50)

            # Display all requirements
            console.print("\n[bold]All Requirements Data:[/bold]")
            for key, value in requirements.items():
                if key == "selected_objectives":
                    console.print(f"  {key}: {len(value)} objectives")
                    for i, obj in enumerate(value[:3], 1):
                        console.print(f"    {i}. {obj}")
                    if len(value) > 3:
                        console.print(f"    ... and {len(value) - 3} more")
                elif key == "standard":
                    console.print(f"  {key}: {value}")
                    if hasattr(value, "__dict__"):
                        console.print(f"    Attributes: {value.__dict__}")
                else:
                    console.print(f"  {key}: {value}")

            # Check standard specifically
            console.print(f"\n[bold]Standard Investigation:[/bold]")
            standard = requirements.get("standard")
            if standard:
                console.print(f"  Standard type: {type(standard)}")
                if hasattr(standard, "standard_id"):
                    console.print(f"  Standard ID: {standard.standard_id}")
                if hasattr(standard, "__dict__"):
                    console.print(f"  Standard dict: {standard.__dict__}")
            else:
                console.print("  ❌ No standard found in requirements")

            # Check objectives
            console.print(f"\n[bold]Objectives Investigation:[/bold]")
            objectives = requirements.get("selected_objectives", [])
            console.print(f"  Objectives count: {len(objectives)}")
            for i, obj in enumerate(objectives, 1):
                console.print(f"    {i}. Type: {type(obj)}")
                if hasattr(obj, "objective_id"):
                    console.print(f"       ID: {obj.objective_id}")
                if hasattr(obj, "objective_text"):
                    console.print(f"       Text: {obj.objective_text[:100]}...")
                if hasattr(obj, "__dict__"):
                    console.print(f"       Dict: {obj.__dict__}")

            # Sample lesson analysis
            console.print(f"\n[bold]Lesson Sample Analysis:[/bold]")
            if lesson:
                # Look for standard patterns
                import re

                # Check for standard codes
                standard_patterns = [
                    r"\b1\.CN\.1\b",
                    r"\b1\.CN\.1\.1\b",
                    r"1\.CN\.1",
                    "1.CN.1.1",
                ]

                console.print(f"  Lesson length: {len(lesson)} characters")
                console.print(f"  First 500 chars:")
                console.print(f"    {lesson[:500]}...")

                console.print(f"\n  Standard code search:")
                for pattern in standard_patterns:
                    matches = re.findall(pattern, lesson, re.IGNORECASE)
                    console.print(f"    Pattern '{pattern}': {len(matches)} matches")
                    if matches:
                        console.print(f"      Found: {matches[:3]}")

                # Check for objective language
                obj_patterns = [
                    r"objective",
                    r"learning.*goal",
                    r"outcome",
                    r"student.*will",
                ]

                console.print(f"\n  Objective language search:")
                for pattern in obj_patterns:
                    matches = re.findall(pattern, lesson, re.IGNORECASE)
                    console.print(f"    Pattern '{pattern}': {len(matches)} matches")

        else:
            console.print(f"❌ Failed to complete conversation: {agent.get_state()}")

    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_lesson_requirements()
