#!/usr/bin/env python3
"""Simple test of lesson generation through conversation flow"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_conversation_flow():
    """Test lesson generation through conversation flow"""

    console.print(
        "\n[bold cyan]Testing Lesson Generation Conversation Flow[/bold cyan]"
    )
    console.print("=" * 60)

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

        console.print("✓ Agent initialized successfully")

        # Test conversation flow
        console.print("\n🤖 Starting conversation flow...")

        # Welcome message
        response = agent.chat("")
        console.print(f"\n[bold]Welcome Response:[/bold]")
        console.print(response[:200] + "..." if len(response) > 200 else response)

        # Simulate grade selection (Kindergarten = option 1)
        console.print("\n📝 Selecting Kindergarten...")
        response = agent.chat("1")
        console.print(f"[bold]Grade Selection Response:[/bold]")
        console.print(response[:200] + "..." if len(response) > 200 else response)

        # Simulate strand selection (Connect = option 1)
        console.print("\n📝 Selecting Connect strand...")
        response = agent.chat("1")
        console.print(f"[bold]Strand Selection Response:[/bold]")
        console.print(response[:200] + "..." if len(response) > 200 else response)

        # Simulate standard selection (K.CN.1 = option 1)
        console.print("\n📝 Selecting K.CN.1 standard...")
        response = agent.chat("1")
        console.print(f"[bold]Standard Selection Response:[/bold]")
        console.print(response[:200] + "..." if len(response) > 200 else response)

        # Check if we reached objective selection or complete
        current_state = agent.get_state()
        console.print(f"\n[bold]Current State:[/bold] {current_state}")

        if current_state == "objective_refinement":
            # Select first objective
            console.print("\n📝 Selecting first objective...")
            response = agent.chat("1")
            console.print(f"[bold]Objective Selection Response:[/bold]")
            console.print(response[:200] + "..." if len(response) > 200 else response)

        # Add context
        current_state = agent.get_state()
        if current_state == "context_collection":
            console.print("\n📝 Adding context...")
            response = agent.chat(
                "Focus on world music examples and movement activities"
            )
            console.print(f"[bold]Context Response:[/bold]")
            console.print(response[:200] + "..." if len(response) > 200 else response)

        # Check final state
        final_state = agent.get_state()
        console.print(f"\n[bold]Final State:[/bold] {final_state}")

        if final_state == "complete":
            lesson = agent.get_generated_lesson()
            requirements = agent.get_lesson_requirements()

            console.print("\n[green]✅ Lesson generation completed![/green]")

            # Show requirements
            console.print(f"\n[bold]Lesson Requirements:[/bold]")
            console.print(f"  Grade: {requirements.get('grade_level', 'N/A')}")
            console.print(f"  Strand: {requirements.get('strand_code', 'N/A')}")
            console.print(f"  Standard: {requirements.get('standard_id', 'N/A')}")
            console.print(
                f"  Objectives: {len(requirements.get('selected_objectives', []))}"
            )

            # Show lesson preview
            if lesson:
                console.print(f"\n[bold]Generated Lesson Preview:[/bold]")
                console.print(lesson[:500] + "..." if len(lesson) > 500 else lesson)
                return True, lesson
            else:
                console.print("[yellow]⚠️  No lesson content generated[/yellow]")
                return False, None
        else:
            console.print(
                f"[yellow]⚠️  Conversation stopped at state: {final_state}[/yellow]"
            )
            return False, None

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False, None


def main():
    """Run the lesson generation test"""

    console.print(
        Panel.fit(
            "[bold blue]Lesson Generation Conversation Test[/bold blue]\n"
            "Testing the conversation-based lesson generation flow",
            border_style="blue",
        )
    )

    success, lesson = test_conversation_flow()

    console.print("\n" + "=" * 60)
    console.print("[bold]Test Result[/bold]")
    console.print("=" * 60)

    if success:
        console.print("[green]✅ PASSED: Lesson generation successful[/green]")
        console.print(f"Lesson length: {len(lesson) if lesson else 0} characters")
        return 0
    else:
        console.print("[red]✗ FAILED: Lesson generation failed[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
