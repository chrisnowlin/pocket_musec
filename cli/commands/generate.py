"""Generate commands for pocket_musec"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import typer
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from typing import Optional, Tuple

from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.llm.chutes_client import ChutesClient
from backend.utils.editor_integration import EditorIntegration
from backend.utils.draft_history import DraftHistoryManager, DraftMetadata
from backend.utils.error_handling import handle_keyboard_interrupts, recovery_manager
from backend.utils.logging_config import get_logger
from backend.utils.progress import ProgressTracker

generate_app = typer.Typer(help="Generate lesson plans and content")
console = Console()
logger = get_logger("generate_command")


@generate_app.command()
@handle_keyboard_interrupts
def lesson(
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Run in interactive mode"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save lesson to file")
):
    """Generate a lesson plan through interactive conversation"""
    
    logger.info("Starting lesson generation command", context={
        'interactive': interactive,
        'output_file': output
    })
    
    try:
        if interactive:
            run_interactive_lesson_generation(output)
        else:
            console.print("[red]Non-interactive mode not yet implemented[/red]")
            console.print("Use --interactive to generate lessons through conversation")
    except Exception as e:
        logger.error("Lesson generation command failed", error=e)
        recovery_manager.log_error(e, {'command': 'lesson', 'interactive': interactive})
        raise


@handle_keyboard_interrupts
def run_interactive_lesson_generation(output: Optional[str] = None):
    """Run the interactive lesson generation conversation"""
    
    logger.info("Starting interactive lesson generation", context={'output_file': output})
    
    with logger.log_performance("interactive_lesson_generation"):
        console.print(Panel.fit(
            Text("🎵 PocketMusec Lesson Generator", style="bold blue"),
            subtitle="AI-powered lesson planning for music teachers"
        ))
        
        # Initialize the lesson agent and draft history manager
        flow = Flow()
        store = Store()
        standards_repo = StandardsRepository()
        llm_client = ChutesClient()
        draft_manager = DraftHistoryManager()
        
        try:
            agent = LessonAgent(flow, store, standards_repo, llm_client)
            
            # Start the conversation
            console.print("\n[green]Starting lesson generation conversation...[/green]\n")
            logger.info("Lesson generation conversation started")
            
            # Main conversation loop
            while agent.get_state() != "complete":
                # Get current response from agent
                if agent.get_state() == "welcome":
                    response = agent.chat("")
                else:
                    # Get user input
                    user_input = get_user_input_for_state(agent.get_state())
                    if user_input is None:  # User wants to quit
                        logger.info("User quit lesson generation")
                        break
                    response = agent.chat(user_input)
                
                # Display agent response
                display_agent_response(response, agent.get_state())
            
            # Handle completed lesson
            if agent.get_state() == "complete":
                handle_completed_lesson(agent, output, draft_manager)
                
        except KeyboardInterrupt:
            logger.info("Lesson generation cancelled by user")
            # Let the decorator handle this
            raise
        except Exception as e:
            logger.error("Error during lesson generation", error=e, context={
                'agent_state': agent.get_state() if 'agent' in locals() else 'unknown'
            })
            recovery_manager.log_error(e, {'operation': 'lesson_generation'})
            console.print(f"\n[red]Error during lesson generation: {str(e)}[/red]")
            raise
        finally:
            # Always cleanup draft history workspace
            try:
                draft_manager.cleanup_workspace()
                logger.debug("Draft workspace cleaned up successfully")
            except Exception as e:
                logger.warning("Failed to cleanup draft workspace", error=e)


def get_user_input_for_state(state: str) -> Optional[str]:
    """Get user input based on current conversation state"""
    
    state_prompts = {
        "grade_selection": "Please select a grade level (enter number) or command: ",
        "strand_selection": "Please select a strand (enter number) or command: ",
        "standard_selection": "Please select a standard (enter number) or describe your topic: ",
        "objective_refinement": "Please select an objective (enter number) or command: ",
        "context_collection": "Enter additional context (or 'skip' to continue): ",
    }
    
    prompt_text = state_prompts.get(state, "Your input: ")
    
    try:
        user_input = Prompt.ask(prompt_text)
        
        # Handle navigation commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            if Confirm.ask("Are you sure you want to quit lesson generation?"):
                return None
        
        return user_input
        
    except KeyboardInterrupt:
        return None


def display_agent_response(response: str, state: str):
    """Display the agent's response with appropriate formatting"""
    
    # Format response based on state
    if state == "welcome":
        console.print(Panel(response, title="Welcome", border_style="blue"))
    elif state == "complete":
        console.print(Panel(response, title="Lesson Complete", border_style="green"))
    elif "Error" in response:
        console.print(Panel(response, title="Error", border_style="red"))
    else:
        console.print(response)


def handle_completed_lesson(agent: LessonAgent, output: Optional[str], draft_manager: DraftHistoryManager):
    """Handle the completed lesson generation"""
    
    lesson = agent.get_generated_lesson()
    requirements = agent.get_lesson_requirements()
    
    if not lesson:
        console.print("[red]No lesson was generated. Please try again.[/red]")
        return

    console.print("\n[green]✅ Lesson generated successfully![/green]\n")
    
    # Create original draft in history
    original_draft = draft_manager.create_draft(
        content=lesson,
        grade_level=requirements.get('grade_level', 'N/A'),
        strand_code=requirements.get('strand_code', 'N/A'),
        strand_name=requirements.get('strand_info', {}).get('name', 'N/A'),
        standard_id=_safe_standard_attribute(requirements, 'standard_id'),
        objectives_count=len(requirements.get('selected_objectives', [])),
        is_original=True
    )
    
    console.print(f"[dim]💾 Original draft saved as: {original_draft.draft_id}[/dim]\n")
    
    # Display lesson summary
    console.print(Panel.fit(
        f"[bold]Grade:[/bold] {requirements.get('grade_level', 'N/A')}\n"
        f"[bold]Strand:[/bold] {requirements.get('strand_code', 'N/A')} - {requirements.get('strand_info', {}).get('name', 'N/A')}\n"
        f"[bold]Standard:[/bold] {_safe_standard_attribute(requirements, 'standard_id')}\n"
        f"[bold]Objectives:[/bold] {len(requirements.get('selected_objectives', []))} selected",
        title="Lesson Summary",
        border_style="cyan"
    ))
    
    # Ask if user wants to see the full lesson
    if Confirm.ask("Would you like to view the complete lesson?"):
        console.print("\n" + "="*60)
        console.print(Panel(lesson, title="Generated Lesson", border_style="green"))
        console.print("="*60)

    current_content = lesson
    aborted_edit = False

    # Ask if user wants to edit the lesson
    if Confirm.ask("Would you like to edit this lesson in your default editor?"):
        current_content, aborted_edit = _run_post_edit_workflow(
            agent, requirements, draft_manager, current_content
        )

    if aborted_edit:
        console.print("[yellow]Lesson edit session cancelled. No changes were saved.[/yellow]")
    else:
        save_path: Optional[Path] = None

        if output:
            save_path = _resolve_output_path(output, requirements)
        elif Confirm.ask("Would you like to save this lesson to a file?"):
            save_path = _prompt_save_path(_default_filename(requirements))

        if save_path:
            save_lesson_to_file(current_content, requirements, save_path)

    # Display session summary
    display_session_summary(draft_manager)
    
    console.print("\n[blue]Thank you for using PocketMusec Lesson Generator![/blue]")


def edit_lesson_with_editor(
    lesson: str, requirements: dict, draft_manager: DraftHistoryManager
) -> Tuple[Optional[str], Optional[DraftMetadata]]:
    """Edit the lesson using system editor"""

    editor = EditorIntegration()
    file_path: Optional[Path] = None

    try:
        # Create lesson content with metadata
        content = f"""# Music Education Lesson Plan

## Lesson Information
- **Grade Level:** {requirements.get('grade_level', 'N/A')}
- **Strand:** {requirements.get('strand_code', 'N/A')} - {requirements.get('strand_info', {}).get('name', 'N/A')}
- **Standard:** {_safe_standard_attribute(requirements, 'standard_id')}
- **Standard Text:** {_safe_standard_attribute(requirements, 'standard_text')}

## Learning Objectives
"""

        objectives = requirements.get('selected_objectives', [])
        if objectives:
            for i, obj in enumerate(objectives, 1):
                content += f"{i}. {obj.objective_text}\n"
        else:
            content += "No specific objectives selected.\n"

        content += f"""
## Additional Context
{requirements.get('additional_context', 'None provided')}

## Generated Lesson Plan

{lesson}

---
Generated by PocketMusec Lesson Generator
"""

        # Create temporary file
        file_path, original_hash = editor.create_temp_file(content)

        console.print(f"\n[yellow]Opening lesson in editor: {editor.detected_editor}[/yellow]")
        console.print(f"[dim]File: {file_path}[/dim]")
        console.print("[dim]Make your changes and save the file, then close the editor to continue.[/dim]\n")

        # Launch editor
        success = editor.launch_editor(file_path)

        if not success:
            console.print("[red]Failed to launch editor. Please check your editor configuration.[/red]")
            return None, None

        # Check for changes
        has_changed, _ = editor.detect_file_changes(file_path, original_hash)

        if has_changed:
            # Read edited content
            with open(file_path, 'r', encoding='utf-8') as f:
                edited_content = f.read()

            # Create new draft in history
            edited_draft = draft_manager.create_draft(
                content=edited_content,
                grade_level=requirements.get('grade_level', 'N/A'),
                strand_code=requirements.get('strand_code', 'N/A'),
                strand_name=requirements.get('strand_info', {}).get('name', 'N/A'),
                standard_id=_safe_standard_attribute(requirements, 'standard_id'),
                objectives_count=len(requirements.get('selected_objectives', [])),
                is_original=False
            )

            console.print("[green]✅ Lesson edited successfully![/green]")
            console.print(f"[dim]💾 Edited draft saved as: {edited_draft.draft_id}[/dim]")

            return edited_content, edited_draft
        else:
            console.print("[yellow]No changes made to the lesson.[/yellow]")
            return None, None

    except Exception as e:
        console.print(f"[red]Error during editing: {str(e)}[/red]")
        return None, None
    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass


def _run_post_edit_workflow(
    agent: LessonAgent,
    requirements: dict,
    draft_manager: DraftHistoryManager,
    lesson_content: str
) -> Tuple[str, bool]:
    """Allow the user to re-edit, regenerate, or cancel after the editor session."""

    current_content = lesson_content
    edited_content, _ = edit_lesson_with_editor(current_content, requirements, draft_manager)
    if edited_content:
        current_content = edited_content
    else:
        console.print("[dim]No changes were detected. You can continue editing or regenerate the lesson.[/dim]")

    aborted = False
    while True:
        choice = Prompt.ask(
            "What would you like to do next?",
            choices=["save", "view", "edit", "regenerate", "cancel"],
            default="save"
        )

        if choice == "save":
            break
        elif choice == "view":
            console.print("\n" + "=" * 60)
            console.print(Panel(current_content, title="Current Lesson", border_style="blue"))
            console.print("=" * 60)
        elif choice == "edit":
            more_edited_content, _ = edit_lesson_with_editor(current_content, requirements, draft_manager)
            if more_edited_content:
                current_content = more_edited_content
        elif choice == "regenerate":
            console.print("[yellow]Regenerating lesson plan with the same requirements...[/yellow]")
            try:
                current_content = agent.regenerate_lesson_plan()
                regenerated_draft = draft_manager.create_draft(
                    content=current_content,
                    grade_level=requirements.get('grade_level', 'N/A'),
                    strand_code=requirements.get('strand_code', 'N/A'),
                    strand_name=requirements.get('strand_info', {}).get('name', 'N/A'),
                    standard_id=_safe_standard_attribute(requirements, 'standard_id'),
                    objectives_count=len(requirements.get('selected_objectives', [])),
                    is_original=False
                )
                console.print(f"[dim]💾 Regenerated draft saved as: {regenerated_draft.draft_id}[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to regenerate lesson: {e}[/red]")
        else:  # cancel
            aborted = True
            break

    return current_content, aborted


def display_session_summary(draft_manager: DraftHistoryManager):
    """Display summary of all drafts created during the session"""
    
    drafts = draft_manager.list_drafts()
    
    if not drafts:
        return
    
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        Text("📋 Session Summary", style="bold cyan"),
        subtitle="Draft history for this lesson generation session"
    ))
    
    # Create summary table
    console.print("\n[bold]Drafts Created:[/bold]")
    console.print("")
    
    # Table header
    console.print(f"{'Draft ID':<12} {'Timestamp':<10} {'Grade':<12} {'Strand':<6} {'Standard':<10} {'Edited':<7}")
    console.print("-" * 70)
    
    # Table rows
    for draft in drafts:
        timestamp = draft.timestamp.strftime("%H:%M:%S")
        edited = "Yes" if draft.has_edits else "No"
        console.print(f"{draft.draft_id:<12} {timestamp:<10} {draft.grade_level:<12} {draft.strand_code:<6} {draft.standard_id:<10} {edited:<7}")
    
    console.print("-" * 70)
    console.print(f"[dim]Total drafts: {len(drafts)} | Session ID: {draft_manager.session_id}[/dim]")
    console.print("="*60)


def save_lesson_to_file(lesson: str, requirements: dict, target_path: Path | str):
    """Save the generated lesson to a file"""
    
    try:
        path = Path(target_path).expanduser()
        if path.is_dir():
            path = path / _default_filename(requirements)
        
        if path.suffix == "":
            path = path.with_suffix(".md")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        content = f"""# Music Education Lesson Plan

## Lesson Information
- **Grade Level:** {requirements.get('grade_level', 'N/A')}
- **Strand:** {requirements.get('strand_code', 'N/A')} - {requirements.get('strand_info', {}).get('name', 'N/A')}
- **Standard:** {_safe_standard_attribute(requirements, 'standard_id')}
- **Standard Text:** {_safe_standard_attribute(requirements, 'standard_text')}

## Learning Objectives
"""
        
        objectives = requirements.get('selected_objectives', [])
        if objectives:
            for i, obj in enumerate(objectives, 1):
                content += f"{i}. {obj.objective_text}\n"
        else:
            content += "No specific objectives selected.\n"
        
        content += f"""
## Additional Context
{requirements.get('additional_context', 'None provided')}

## Generated Lesson Plan

{lesson}

---
Generated by PocketMusec Lesson Generator
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✅ Lesson saved to {path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error saving lesson: {str(e)}[/red]")


def _prompt_save_path(default_name: str) -> Path:
    """Prompt the user for a filename or path to save the lesson"""

    while True:
        user_input = Prompt.ask(
            f"Enter filename or path to save (press enter to use {default_name})",
            default=default_name
        )

        candidate = Path(user_input).expanduser()
        if candidate.is_dir():
            candidate = candidate / default_name

        if candidate.suffix == "":
            candidate = candidate.with_suffix(".md")

        parent = candidate.parent
        if not parent.exists():
            if Confirm.ask(f"Directory {parent} does not exist. Create it?"):
                parent.mkdir(parents=True, exist_ok=True)
            else:
                continue

        return candidate


def _resolve_output_path(output: str, requirements: dict) -> Path:
    """Resolve --output paths, creating directories when needed"""

    path = Path(output).expanduser()
    if path.is_dir():
        path = path / _default_filename(requirements)

    if path.suffix == "":
        path = path.with_suffix(".md")

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _default_filename(requirements: dict) -> str:
    """Build a default filename from the lesson metadata"""

    grade_slug = _slugify_for_filename(requirements.get('grade_level', 'lesson'))
    standard_slug = _slugify_for_filename(_safe_standard_attribute(requirements, 'standard_id'))
    return f"{grade_slug}_{standard_slug}.md"


def _safe_standard_attribute(requirements: dict, attr: str, default: str = "N/A") -> str:
    """Safely access attributes from either dict or dataclass standard representations"""

    standard = requirements.get('standard')
    if isinstance(standard, dict):
        return standard.get(attr, default)
    return getattr(standard, attr, default) if standard else default


def _slugify_for_filename(value: str) -> str:
    """Create a filename-safe slug from a string"""

    cleaned = "".join(c.lower() if c.isalnum() else "_" for c in value)
    return cleaned.strip("_") or "lesson"
