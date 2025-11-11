"""Lesson generation agent for PocketFlow framework"""

from typing import Any, Dict, List, Optional, Tuple
from backend.pocketflow.agent import Agent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.models import Standard, Objective, StandardWithObjectives
from backend.llm.chutes_client import ChutesClient
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates


class LessonAgent(Agent):
    """Agent for generating music education lessons through conversation"""

    def __init__(
        self,
        flow: Flow,
        store: Store,
        standards_repo: Optional[StandardsRepository] = None,
        llm_client: Optional[ChutesClient] = None,
    ):
        super().__init__(flow, store, "LessonAgent")
        self.standards_repo = standards_repo or StandardsRepository()
        self.llm_client = llm_client or ChutesClient()
        self.prompt_templates = LessonPromptTemplates()

        # Initialize conversation state
        self.lesson_requirements: Dict[str, Any] = {}

        # Set up state handlers
        self._setup_state_handlers()

        # Start with welcome state
        self.set_state("welcome")

    def _setup_state_handlers(self) -> None:
        """Set up handlers for each conversation state"""
        self.add_state_handler("welcome", self._handle_welcome)
        self.add_state_handler("grade_selection", self._handle_grade_selection)
        self.add_state_handler("strand_selection", self._handle_strand_selection)
        self.add_state_handler("standard_selection", self._handle_standard_selection)
        self.add_state_handler(
            "objective_refinement", self._handle_objective_refinement
        )
        self.add_state_handler("context_collection", self._handle_context_collection)
        self.add_state_handler("lesson_generation", self._handle_lesson_generation)
        self.add_state_handler("complete", self._handle_complete)

    def _show_welcome_message(self) -> str:
        """Show welcome message without changing state"""
        grade_levels = self.standards_repo.get_grade_levels()

        response = (
            "🎵 Welcome to PocketMusec Lesson Generator!\n\n"
            "I'll help you create a standards-aligned music education lesson. "
            "Let's start by selecting a grade level.\n\n"
            "Available grade levels:\n"
        )

        for i, grade in enumerate(grade_levels, 1):
            response += f"{i}. {grade}\n"

        response += (
            "\nPlease enter a number (1-"
            + str(len(grade_levels))
            + ") or type 'quit' to exit."
        )

        return response

    def _handle_welcome(self, message: str) -> str:
        """Handle welcome state and grade selection"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        # Show welcome message and move to grade selection
        response = self._show_welcome_message()
        self.set_state("grade_selection")

        return response

    def _handle_grade_selection(self, message: str) -> str:
        """Handle grade level selection"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("welcome")
            return self._show_welcome_message()

        try:
            grade_levels = self.standards_repo.get_grade_levels()
            choice = int(message.strip())

            if 1 <= choice <= len(grade_levels):
                selected_grade = grade_levels[choice - 1]
                self.lesson_requirements["grade_level"] = selected_grade

                # Move to strand selection
                self.set_state("strand_selection")
                return self._show_strand_options()
            else:
                return f"Please enter a number between 1 and {len(grade_levels)}."

        except ValueError:
            return "Please enter a valid number or 'quit' to exit."

    def _show_strand_options(self) -> str:
        """Show available strand options"""
        grade = self.lesson_requirements["grade_level"]
        standards = self.standards_repo.get_standards_by_grade(grade)
        strand_info = self.standards_repo.get_strand_info()

        # Get unique strands available for this grade
        available_strands = {}
        for standard in standards:
            if standard.strand_code not in available_strands:
                available_strands[standard.strand_code] = strand_info.get(
                    standard.strand_code, {}
                )

        response = f"📚 Grade {grade} - Select a Strand\n\nAvailable strands:\n"

        strand_list = list(available_strands.keys())
        for i, strand_code in enumerate(strand_list, 1):
            info = available_strands[strand_code]
            response += f"{i}. {strand_code} - {info.get('name', 'Unknown')}\n"
            response += f"   {info.get('description', 'No description')}\n\n"

        response += f"Please enter a number (1-{len(strand_list)}) or type 'back' to return to grade selection."

        return response

    def _handle_strand_selection(self, message: str) -> str:
        """Handle strand selection"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("grade_selection")
            return self._handle_welcome("")

        if not message.strip():
            return self._show_strand_options()

        try:
            grade = self.lesson_requirements["grade_level"]
            standards = self.standards_repo.get_standards_by_grade(grade)
            strand_info = self.standards_repo.get_strand_info()

            # Get unique strands available for this grade
            available_strands = {}
            for standard in standards:
                if standard.strand_code not in available_strands:
                    available_strands[standard.strand_code] = strand_info.get(
                        standard.strand_code, {}
                    )

            strand_list = list(available_strands.keys())
            choice = int(message.strip())

            if 1 <= choice <= len(strand_list):
                selected_strand = strand_list[choice - 1]
                self.lesson_requirements["strand_code"] = selected_strand
                self.lesson_requirements["strand_info"] = available_strands[
                    selected_strand
                ]

                # Move to standard selection
                self.set_state("standard_selection")
                return self._show_standard_options()
            else:
                return f"Please enter a number between 1 and {len(strand_list)}."

        except ValueError:
            return "Please enter a valid number or 'back' to return to grade selection."

    def _show_standard_options(self) -> str:
        """Show available standard options"""
        grade = self.lesson_requirements["grade_level"]
        strand = self.lesson_requirements["strand_code"]

        # Get standards for this grade and strand
        standards = self.standards_repo.get_standards_by_grade_and_strand(grade, strand)

        response = f"🎯 {grade} - {strand} Standards\n\nAvailable standards:\n"

        for i, standard in enumerate(standards, 1):
            response += f"{i}. {standard.standard_id}\n"
            response += f"   {standard.standard_text[:100]}{'...' if len(standard.standard_text) > 100 else ''}\n\n"

        response += (
            "Please enter a number to select a standard, "
            "or type a topic/idea for recommendations, "
            "or 'back' to return to strand selection."
        )

        return response

    def _handle_standard_selection(self, message: str) -> str:
        """Handle standard selection and recommendation"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("strand_selection")
            return self._show_strand_options()

        if not message.strip():
            return self._show_standard_options()

        grade = self.lesson_requirements["grade_level"]
        strand = self.lesson_requirements["strand_code"]
        standards = self.standards_repo.get_standards_by_grade_and_strand(grade, strand)

        # Check if user entered a number (direct selection)
        try:
            choice = int(message.strip())
            if 1 <= choice <= len(standards):
                selected_standard = standards[choice - 1]
                self.lesson_requirements["standard"] = selected_standard

                # Get objectives for this standard
                objectives = self.standards_repo.get_objectives_for_standard(
                    selected_standard.standard_id
                )
                self.lesson_requirements["objectives"] = objectives

                # Move to objective refinement
                self.set_state("objective_refinement")
                return self._show_objective_options()
            else:
                return f"Please enter a number between 1 and {len(standards)} or describe your lesson topic."
        except ValueError:
            # User entered a topic - provide recommendations
            topic = message.strip()
            recommendations = self.standards_repo.recommend_standards_for_topic(
                topic, grade, limit=5
            )

            if not recommendations:
                return "No standards found for that topic. Please try a different topic or select from the list."

            response = f"🔍 Recommended standards for '{topic}':\n\n"

            for i, (standard, score) in enumerate(recommendations, 1):
                response += f"{i}. {standard.standard_id} (Relevance: {score:.2f})\n"
                response += f"   {standard.standard_text[:100]}{'...' if len(standard.standard_text) > 100 else ''}\n\n"

            response += (
                "Please enter a number to select a standard or try a different topic."
            )

            return response

    def _show_objective_options(self) -> str:
        """Show available objective options"""
        objectives = self.lesson_requirements["objectives"]
        standard = self.lesson_requirements["standard"]

        if not objectives:
            # No objectives available, skip to context collection
            self.set_state("context_collection")
            return self._handle_context_collection("")

        response = (
            f"📋 {standard.standard_id} - Learning Objectives\n\n"
            "Available objectives:\n"
        )

        for i, objective in enumerate(objectives, 1):
            response += f"{i}. {objective.objective_text}\n\n"

        response += (
            "Please enter a number to select an objective, "
            "or type 'all' to use all objectives, "
            "or 'skip' to continue without specific objectives, "
            "or 'back' to return to standard selection."
        )

        return response

    def _handle_objective_refinement(self, message: str) -> str:
        """Handle objective selection and refinement"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("standard_selection")
            return self._show_standard_options()

        objectives = self.lesson_requirements["objectives"]
        standard = self.lesson_requirements["standard"]

        if not objectives:
            # No objectives available, skip to context collection
            self.lesson_requirements["selected_objectives"] = []
            self.set_state("context_collection")
            return self._handle_context_collection("")

        if not message.strip():
            return self._show_objective_options()

        if message.lower() == "all":
            self.lesson_requirements["selected_objectives"] = objectives
            self.set_state("context_collection")
            return self._handle_context_collection("")

        if message.lower() == "skip":
            self.lesson_requirements["selected_objectives"] = []
            self.set_state("context_collection")
            return self._handle_context_collection("")

        try:
            choice = int(message.strip())
            if 1 <= choice <= len(objectives):
                selected_objective = objectives[choice - 1]
                self.lesson_requirements["selected_objectives"] = [selected_objective]

                self.set_state("context_collection")
                return self._handle_context_collection("")
            else:
                return f"Please enter a number between 1 and {len(objectives)} or 'all', 'skip', or 'back'."
        except ValueError:
            return "Please enter a valid number, 'all', 'skip', or 'back'."

    def _handle_context_collection(self, message: str) -> str:
        """Handle optional context collection"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Lesson generation cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            if self.lesson_requirements.get("objectives"):
                self.set_state("objective_refinement")
                return self._show_objective_options()
            else:
                self.set_state("standard_selection")
                return self._show_standard_options()

        if not message.strip():
            # First time showing context options
            response = (
                "🎨 Additional Context (Optional)\n\n"
                "You can provide additional context to help customize the lesson:\n"
                "- Specific topics or themes\n"
                "- Available resources or instruments\n"
                "- Student needs or interests\n"
                "- Time constraints\n"
                "- Any other relevant information\n\n"
                "Type your context or 'skip' to continue without additional context, "
                "or 'back' to return to objective selection."
            )

            return response

        if message.lower() in ["skip", "done", "continue"]:
            # Skip context collection and generate lesson
            self.set_state("lesson_generation")
            return self._generate_lesson()

        # Store the context and continue
        self.lesson_requirements["additional_context"] = message.strip()
        self.set_state("lesson_generation")
        return self._generate_lesson()

    def _handle_lesson_generation(self, message: str) -> str:
        """Handle lesson generation state"""
        return self._generate_lesson()

    def _request_lesson_plan(self) -> str:
        """Request a lesson plan from the LLM client."""
        context = self._build_lesson_context()
        lesson_plan = self.llm_client.generate_lesson_plan(context)
        self.lesson_requirements["generated_lesson"] = lesson_plan
        return lesson_plan

    def _generate_lesson(self) -> str:
        """Generate the lesson plan using LLM"""
        try:
            lesson_plan = self._request_lesson_plan()

            # Store the generated lesson
            self.set_state("complete")

            return (
                "🎉 Lesson Generated Successfully!\n\n"
                f"{lesson_plan}\n\n"
                "Lesson generation complete. You can now save this lesson "
                "or make any needed edits."
            )
        except Exception as e:
            return f"❌ Error generating lesson: {str(e)}\n\nPlease try again or contact support."

    def regenerate_lesson_plan(self) -> str:
        """Regenerate the lesson plan using existing requirements."""
        self.set_state("lesson_generation")
        try:
            lesson_plan = self._request_lesson_plan()
            self.set_state("complete")
            return lesson_plan
        except Exception:
            self.set_state("complete")
            raise

    def _build_lesson_context(self) -> LessonPromptContext:
        """Build context dictionary for lesson generation"""
        objective_texts = [
            obj.objective_text
            for obj in self.lesson_requirements.get("selected_objectives", [])
        ]

        return LessonPromptContext(
            grade_level=self.lesson_requirements["grade_level"],
            strand_code=self.lesson_requirements["strand_code"],
            strand_name=self.lesson_requirements["strand_info"].get("name", ""),
            strand_description=self.lesson_requirements["strand_info"].get(
                "description", ""
            ),
            standard_id=self.lesson_requirements["standard"].standard_id,
            standard_text=self.lesson_requirements["standard"].standard_text,
            objectives=objective_texts,
            additional_context=self.lesson_requirements.get("additional_context"),
        )

    def _handle_complete(self, message: str) -> str:
        """Handle completion state"""
        return "Lesson generation is complete. Thank you for using PocketMusec!"

    def get_lesson_requirements(self) -> Dict[str, Any]:
        """Get the collected lesson requirements"""
        return self.lesson_requirements.copy()

    def get_generated_lesson(self) -> Optional[str]:
        """Get the generated lesson plan"""
        return self.lesson_requirements.get("generated_lesson")

    def reset_conversation(self) -> None:
        """Reset the conversation for a new lesson"""
        self.lesson_requirements.clear()
        self.clear_history()
        self.set_state("welcome")

    def serialize_state(self) -> str:
        """Serialize agent state to JSON for persistence"""
        import json

        # Convert requirements to serializable format
        serializable_reqs = {}
        for key, value in self.lesson_requirements.items():
            if key == "standard":
                # Serialize standard object
                if value:
                    serializable_reqs[key] = {
                        "standard_id": value.standard_id,
                        "grade_level": value.grade_level,
                        "strand_code": value.strand_code,
                        "strand_name": value.strand_name,
                        "standard_text": value.standard_text,
                        "strand_description": value.strand_description,
                    }
            elif key == "selected_objectives":
                # Serialize objectives list
                if value:
                    serializable_reqs[key] = [
                        {
                            "objective_id": obj.objective_id,
                            "standard_id": obj.standard_id,
                            "objective_text": obj.objective_text,
                        }
                        for obj in value
                    ]
            elif key in ["strand_info", "recommendations"]:
                # These are already serializable dicts/lists
                serializable_reqs[key] = value
            else:
                # Simple types (str, int, etc.)
                serializable_reqs[key] = value

        state = {
            "current_state": self.get_state(),
            "lesson_requirements": serializable_reqs,
            "conversation_history": self.get_conversation_history(),
        }

        return json.dumps(state)

    def restore_state(self, state_json: str) -> None:
        """Restore agent state from JSON"""
        import json
        from backend.repositories.models import Standard, Objective

        state = json.loads(state_json)

        # Restore current state
        self.set_state(state.get("current_state", "welcome"))

        # Restore lesson requirements
        reqs = state.get("lesson_requirements", {})
        for key, value in reqs.items():
            if key == "standard" and value:
                # Reconstruct Standard object
                self.lesson_requirements[key] = Standard(
                    standard_id=value["standard_id"],
                    grade_level=value["grade_level"],
                    strand_code=value["strand_code"],
                    strand_name=value["strand_name"],
                    standard_text=value["standard_text"],
                    strand_description=value["strand_description"],
                )
            elif key == "selected_objectives" and value:
                # Reconstruct Objective objects
                self.lesson_requirements[key] = [
                    Objective(
                        objective_id=obj["objective_id"],
                        standard_id=obj["standard_id"],
                        objective_text=obj["objective_text"],
                    )
                    for obj in value
                ]
            else:
                self.lesson_requirements[key] = value

        # Restore conversation history
        history = state.get("conversation_history", [])
        self.conversation_history = history
