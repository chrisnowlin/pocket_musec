"""Lesson generation agent for PocketFlow framework"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import json
import re
from backend.pocketflow.agent import Agent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.models import Standard, Objective, StandardWithObjectives
from backend.llm.chutes_client import ChutesClient, Message
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates
import logging

logger = logging.getLogger(__name__)


class LessonAgent(Agent):
    """Agent for generating music education lessons through conversation"""

    def __init__(
        self,
        flow: Flow,
        store: Store,
        standards_repo: Optional[StandardsRepository] = None,
        llm_client: Optional[ChutesClient] = None,
        conversational_mode: bool = True,
    ):
        super().__init__(flow, store, "LessonAgent")
        self.standards_repo = standards_repo or StandardsRepository()
        self.llm_client = llm_client or ChutesClient()
        self.prompt_templates = LessonPromptTemplates()
        self.conversational_mode = conversational_mode

        # Initialize conversation state
        self.lesson_requirements: Dict[str, Any] = {
            "conversation_context": [],
            "extracted_info": {},
            "suggestions_made": [],
            "user_preferences": {},
            "current_focus": None,
        }

        # Set up state handlers
        self._setup_state_handlers()

        # Start with appropriate state
        if conversational_mode:
            self.set_state("conversational_welcome")
        else:
            self.set_state("welcome")

    # Conversational Mode Methods
    def _get_conversational_system_prompt(self) -> str:
        """Get system prompt for conversational lesson planning"""
        return """<role>
 You are an expert music education curriculum specialist and AI assistant for PocketMusec. You help teachers create engaging, standards-aligned music lessons through natural conversation.
</role>

<expertise>
 - Deep knowledge of K-12 music education and North Carolina music standards
 - Expert in lesson planning, pedagogy, and assessment strategies
 - Skilled at understanding teacher needs and providing personalized suggestions
 - Proficient in extracting key information from natural conversation
 - Excellent at making connections between teacher requests and educational standards
</expertise>

<conversation_style>
 - Be warm, professional, and conversational
 - Ask clarifying questions when needed
 - Provide intelligent suggestions based on what teachers share
 - Extract lesson requirements naturally from conversation
 - Offer options and alternatives rather than rigid forms
 - Remember context and build on previous exchanges
 - Be proactive in suggesting relevant standards and activities
</conversation_style>

<information_extraction>
 From teacher conversations, extract and track:
 - Grade level (explicit or implied)
 - Musical concepts, skills, or topics of interest
 - Available time, resources, or constraints
 - Student needs, class size, or special considerations
 - Preferred teaching styles or activity types
 - Any specific standards or curriculum requirements
</information_extraction>"""

    def _analyze_user_message(self, message: str) -> Dict[str, Any]:
        """Use Chutes API to analyze user message and extract information"""
        try:
            analysis_prompt = f"""Analyze this music teacher's message and extract key information for lesson planning:

Message: "{message}"

Extract and return JSON with:
{{
    "grade_level": "specific grade mentioned or implied (or null)",
    "musical_topics": ["list of musical concepts, skills, or topics mentioned"],
    "time_constraints": "any time duration mentioned (or null)",
    "resources": ["any instruments, materials, or technology mentioned"],
    "student_needs": ["any special student considerations mentioned"],
    "activity_preferences": ["types of activities teacher prefers"],
    "intent": "what the teacher wants to accomplish (plan lesson, get ideas, find standards, etc.)",
    "questions_asked": ["any specific questions teacher asked"],
    "confidence_score": "how confident you are in the extraction (0-1)"
}}

Focus on musical education context. If information isn't present, use null."""

            messages = [
                Message(
                    role="system", content=self._get_conversational_system_prompt()
                ),
                Message(role="user", content=analysis_prompt),
            ]

            response = self.llm_client.chat_completion(
                messages=messages, temperature=0.3, max_tokens=500
            )

            # Debug logging to check response type
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response value: {response}")
            
            # Parse the JSON response
            try:
                # Handle both ChatResponse object and dictionary
                if hasattr(response, 'content'):
                    content = response.content
                elif isinstance(response, dict):
                    content = response.get('content', str(response))
                else:
                    content = str(response)
                    
                extracted = json.loads(content)
                return extracted
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse analysis response: {content if 'content' in locals() else response}")
                return {"confidence_score": 0.0}

        except Exception as e:
            logger.error(f"Error analyzing user message: {e}")
            return {"confidence_score": 0.0}

    def _get_relevant_standards(self, extracted_info: Dict[str, Any]) -> List[Standard]:
        """Get relevant standards based on extracted information"""
        grade_level = extracted_info.get("grade_level")
        musical_topics = extracted_info.get("musical_topics", [])

        if not grade_level:
            return []

        # Get all standards for the grade level
        standards = self.standards_repo.get_standards_by_grade(grade_level)

        if not musical_topics:
            return standards[:5]  # Return first 5 if no specific topics

        # Score standards based on topic relevance
        scored_standards = []
        for standard in standards:
            score = 0
            standard_text = standard.standard_text.lower()

            for topic in musical_topics:
                topic_lower = topic.lower()
                if topic_lower in standard_text:
                    score += 1
                # Check for related terms
                if any(
                    related in standard_text
                    for related in self._get_related_terms(topic)
                ):
                    score += 0.5

            if score > 0:
                scored_standards.append((standard, score))

        # Sort by score and return top matches
        scored_standards.sort(key=lambda x: x[1], reverse=True)
        return [standard for standard, _ in scored_standards[:5]]

    def _get_related_terms(self, topic: str) -> List[str]:
        """Get related musical terms for a topic"""
        term_mapping = {
            "rhythm": ["beat", "meter", "tempo", "pattern", "pulse"],
            "melody": ["pitch", "tune", "contour", "interval", "scale"],
            "harmony": ["chord", "accompaniment", "progression", "tonality"],
            "form": ["structure", "aba", "verse", "chorus", "rondo"],
            "timbre": ["tone color", "instrument", "voice", "sound quality"],
            "dynamics": ["loud", "soft", "crescendo", "diminuendo", "volume"],
            "tempo": ["speed", "fast", "slow", "allegro", "adagio"],
            "notation": ["notes", "staff", "clef", "symbols", "reading"],
            "composition": ["creating", "improvising", "writing", "making"],
            "listening": ["analysis", "appreciation", "evaluation", "response"],
            "movement": ["dance", "motion", "body", "kinesthetic"],
            "singing": ["voice", "vocals", "song", "choral"],
            "instruments": ["playing", "performance", "ensemble", "band"],
        }

        topic_lower = topic.lower()
        return term_mapping.get(topic_lower, [])

    def _format_standards_suggestions(self, standards: List[Standard]) -> str:
        """Format standards suggestions with better visual structure"""
        if not standards:
            return ""

        formatted = "\n### 🎯 Relevant Standards for Your Lesson\n\n"
        for i, standard in enumerate(standards[:3], 1):  # Show top 3
            formatted += f"**{i}. {standard.standard_id}** - {standard.strand_name}\n"
            formatted += f"*{standard.standard_text[:120]}{'...' if len(standard.standard_text) > 120 else ''}*\n\n"

        if len(standards) > 3:
            formatted += f"*... and {len(standards) - 3} more relevant standards*\n"

        return formatted

    def _format_activity_suggestions(self, extracted_info: Dict[str, Any]) -> str:
        """Format activity suggestions based on extracted info"""
        suggestions = []

        # Add suggestions based on musical topics
        topics = extracted_info.get("musical_topics", [])
        if topics:
            suggestions.append("### 🎵 Activity Ideas\n\n")
            for topic in topics[:3]:  # Top 3 topics
                topic_lower = topic.lower()
                if "rhythm" in topic_lower:
                    suggestions.append(
                        "• • **Rhythm Circle Time** - Students create rhythmic patterns using body percussion and instruments\n"
                    )
                    suggestions.append(
                        "• • **Beat Detective** - Listen and identify steady beats in music\n"
                    )
                elif "melody" in topic_lower:
                    suggestions.append(
                        "• • **Melody Maker** - Students create simple melodies using xylophones or recorders\n"
                    )
                    suggestions.append(
                        "• • **Pitch Matching Games** - Call and response singing activities\n"
                    )
                elif "harmony" in topic_lower:
                    suggestions.append(
                        "• • **Chord Building** - Explore harmony using classroom instruments\n"
                    )
                    suggestions.append(
                        "• • **Partner Songs** - Simple two-part harmony exercises\n"
                    )

        # Add suggestions based on available resources
        resources = extracted_info.get("resources", [])
        if resources:
            suggestions.append("\n### 🥁 Using Your Available Resources\n\n")
            for resource in resources[:3]:
                suggestions.append(
                    f"• • **{resource.title()} Integration** - Incorporate these instruments throughout the lesson\n"
                )

        return "".join(suggestions)

    def _generate_conversational_response(
        self,
        message: str,
        extracted_info: Dict[str, Any],
        relevant_standards: List[Standard],
    ) -> str:
        """Generate a conversational response using Chutes API"""

        # Build context for response generation
        context_info = {
            "extracted_info": extracted_info,
            "relevant_standards": [
                {
                    "id": std.standard_id,
                    "text": std.standard_text[:150] + "..."
                    if len(std.standard_text) > 150
                    else std.standard_text,
                    "strand": std.strand_name,
                }
                for std in relevant_standards
            ],
            "conversation_history": self.lesson_requirements["conversation_context"][
                -3:
            ],  # Last 3 exchanges
            "current_requirements": self.lesson_requirements["extracted_info"],
        }

        response_prompt = f"""Generate a warm, conversational response to this music teacher. Help them plan their lesson naturally.

Teacher's message: "{message}"

Context from our conversation: {json.dumps(context_info, indent=2)}

Guidelines for your response:
1. Acknowledge what they shared and show understanding
2. Ask thoughtful follow-up questions if needed
3. Suggest relevant standards that match their interests
4. Offer specific activity ideas or teaching strategies
5. Be helpful and encouraging, not rigid or form-like
6. If you have enough information, offer to create a lesson plan
7. Keep it conversational and build on what they've told you

FORMATTING REQUIREMENTS:
- Use emojis to make responses engaging and visually appealing (🎵, 🎶, 🥁, 🎹, 🎤, 🎼, ✨, 💡, 🎯, 📚, 🎨, 🌟)
- Use markdown formatting for better readability:
  - Use **bold** for emphasis on key concepts
  - Use *italics* for activity suggestions
  - Use bullet points (•) for lists of ideas or standards
  - Use section headers with ### for organizing information
- Keep paragraphs short and easy to read
- Use line breaks to separate ideas
- Make it scannable with clear visual hierarchy

Write your response as if you're talking to a fellow music educator. Be warm, knowledgeable, and helpful."""

        messages = [
            Message(role="system", content=self._get_conversational_system_prompt()),
            Message(role="user", content=response_prompt),
        ]

        response = self.llm_client.chat_completion(
            messages=messages, temperature=0.7, max_tokens=800
        )

        # Debug logging to check response type
        logger.debug(f"Generate response type: {type(response)}")
        
        # Enhance the response with better formatting
        # Handle both ChatResponse object and dictionary
        if hasattr(response, 'content'):
            enhanced_response = response.content
        elif isinstance(response, dict):
            enhanced_response = response.get('content', str(response))
        else:
            enhanced_response = str(response)

        # Add formatted standards suggestions if available
        if relevant_standards:
            standards_section = self._format_standards_suggestions(relevant_standards)
            if standards_section and "🎯" not in enhanced_response:
                enhanced_response += "\n" + standards_section

        # Add activity suggestions based on extracted info
        activity_section = self._format_activity_suggestions(extracted_info)
        if activity_section and "🎵" not in enhanced_response:
            enhanced_response += "\n" + activity_section

        # Add a friendly closing if not present
        if (
            "ready to create" in enhanced_response.lower()
            or "generate lesson" in enhanced_response.lower()
        ):
            enhanced_response += "\n\n### 🚀 Ready to Create?\n\nWhen you're ready, just say **'generate lesson plan'** and I'll create a personalized lesson based on our conversation! ✨"

        return enhanced_response

    def _handle_conversational_welcome(self, message: str) -> str:
        """Handle the initial conversational exchange"""
        # Store the message in conversation context
        self.lesson_requirements["conversation_context"].append(
            {"role": "user", "message": message, "timestamp": self._get_timestamp()}
        )

        # Check if this is the very first message
        if len(self.lesson_requirements["conversation_context"]) == 1:
            welcome_header = """# 🎵 Welcome to PocketMusec Lesson Planning!

Hello! I'm your AI music education assistant, and I'm excited to help you create engaging, standards-aligned music lessons!

---

## 💫 How This Works

Simply **tell me about your lesson needs** in natural language, and I'll:
• • *Understand your grade level and musical topics*
• • *Suggest relevant standards automatically*
• • *Recommend activities based on your resources*
• • *Create a personalized lesson plan when you're ready*

---

## 🚀 Let's Get Started!

"""
        else:
            welcome_header = ""

        # Analyze the user's message
        extracted_info = self._analyze_user_message(message)

        # Update extracted information
        self.lesson_requirements["extracted_info"].update(extracted_info)

        # Get relevant standards
        relevant_standards = self._get_relevant_standards(extracted_info)

        # Store standards for later use
        if relevant_standards:
            self.lesson_requirements["suggested_standards"] = relevant_standards

        # Generate conversational response
        response = self._generate_conversational_response(
            message, extracted_info, relevant_standards
        )

        # Combine welcome header with response for first message
        if welcome_header:
            full_response = welcome_header + response
        else:
            full_response = response

        # Store the response
        self.lesson_requirements["conversation_context"].append(
            {
                "role": "assistant",
                "message": full_response,
                "timestamp": self._get_timestamp(),
            }
        )

        # Move to lesson planning state
        self.set_state("lesson_planning")

        return full_response

    def _handle_lesson_planning(self, message: str) -> str:
        """Handle ongoing lesson planning conversation"""
        # Store the message
        self.lesson_requirements["conversation_context"].append(
            {"role": "user", "message": message, "timestamp": self._get_timestamp()}
        )

        # Check if user wants to generate a lesson
        if self._should_generate_lesson(message):
            self.set_state("generation")
            return self._generate_lesson_plan()

        # Analyze the new message
        extracted_info = self._analyze_user_message(message)

        # Update extracted information with new details
        for key, value in extracted_info.items():
            if value and key != "confidence_score":
                existing = self.lesson_requirements["extracted_info"].get(key, [])
                if isinstance(existing, list):
                    # Merge lists, avoiding duplicates
                    if isinstance(value, list):
                        for item in value:
                            if item not in existing:
                                existing.append(item)
                    else:
                        if value not in existing:
                            existing.append(value)
                else:
                    # Update single values
                    self.lesson_requirements["extracted_info"][key] = value

        # Get updated relevant standards
        relevant_standards = self._get_relevant_standards(
            self.lesson_requirements["extracted_info"]
        )

        # Generate conversational response
        response = self._generate_conversational_response(
            message, extracted_info, relevant_standards
        )

        # Store the response
        self.lesson_requirements["conversation_context"].append(
            {
                "role": "assistant",
                "message": response,
                "timestamp": self._get_timestamp(),
            }
        )

        return response

    def _should_generate_lesson(self, message: str) -> bool:
        """Check if user wants to generate a lesson plan"""
        generation_triggers = [
            "generate lesson",
            "create lesson",
            "make lesson",
            "lesson plan",
            "write lesson",
            "develop lesson",
            "create a lesson",
            "make a lesson",
            "generate a lesson",
            "let's create",
            "let's make",
            "ready to create",
            "ready to generate",
            "let's plan",
            "time to create",
            "let's write",
        ]

        message_lower = message.lower()
        return any(trigger in message_lower for trigger in generation_triggers)

    def _generate_lesson_plan(self) -> str:
        """Generate the actual lesson plan using collected information"""
        try:
            # Build lesson context from conversation
            context = self._build_lesson_context_from_conversation()

            # Generate the lesson plan
            lesson_plan = self.llm_client.generate_lesson_plan(context, stream=False)

            # Handle the Union[str, Iterator[str]] return type
            final_plan: str
            if isinstance(lesson_plan, str):
                final_plan = lesson_plan
            else:
                # If it's an iterator, join all chunks
                final_plan = "".join(lesson_plan)

            # Store the generated lesson
            self.lesson_requirements["generated_lesson"] = final_plan
            self.set_state("complete")

            response = f"""# 🎉 Your Personalized Music Lesson Plan

---

{final_plan}

---

## 📝 Lesson Customization Options

This lesson plan was created specifically for you based on our conversation! I can help you refine it further:

**🔧 Adjust & Modify**
• • *Activity timing or sequence*
• • *Difficulty level for your students*
• • *Resource requirements*

**🎯 Enhance Learning**
• • *Differentiation strategies for diverse learners*
• • *Assessment ideas and rubrics*
• • *Cross-curricular connections*

**🎨 Creative Extensions**
• • *Additional activities or projects*
• • *Technology integration ideas*
• • *Performance or sharing opportunities*

---

### 💬 What would you like to refine about this lesson?

Just let me know what adjustments you'd like, and I'll update the plan for you! ✨"""

            # Store the response
            self.lesson_requirements["conversation_context"].append(
                {
                    "role": "assistant",
                    "message": response,
                    "timestamp": self._get_timestamp(),
                }
            )

            return response

        except Exception as e:
            error_msg = f"I encountered an error generating your lesson plan: {str(e)}. Let me try a different approach or you can provide more details about what you'd like included."

            self.lesson_requirements["conversation_context"].append(
                {
                    "role": "assistant",
                    "message": error_msg,
                    "timestamp": self._get_timestamp(),
                }
            )

            return error_msg

    def _build_lesson_context_from_conversation(self) -> LessonPromptContext:
        """Build lesson context from conversational extraction"""
        extracted = self.lesson_requirements["extracted_info"]

        # Get the best standard from suggestions
        standard = None
        objectives = []

        if "suggested_standards" in self.lesson_requirements:
            standard = self.lesson_requirements["suggested_standards"][0]
            objectives = self.standards_repo.get_objectives_for_standard(
                standard.standard_id
            )

        # Build additional context from conversation
        additional_context_parts = []

        if extracted.get("musical_topics"):
            additional_context_parts.append(
                f"Musical focus: {', '.join(extracted['musical_topics'])}"
            )

        if extracted.get("resources"):
            additional_context_parts.append(
                f"Available resources: {', '.join(extracted['resources'])}"
            )

        if extracted.get("student_needs"):
            additional_context_parts.append(
                f"Student considerations: {', '.join(extracted['student_needs'])}"
            )

        if extracted.get("activity_preferences"):
            additional_context_parts.append(
                f"Preferred activities: {', '.join(extracted['activity_preferences'])}"
            )

        return LessonPromptContext(
            grade_level=extracted.get("grade_level", "Grade 3"),
            strand_code=standard.strand_code if standard else "Create",
            strand_name=standard.strand_name if standard else "Create Strand",
            strand_description=standard.strand_description
            if standard
            else "Creating and expressing music",
            standard_id=standard.standard_id if standard else "Custom Lesson",
            standard_text=standard.standard_text
            if standard
            else "Custom lesson based on teacher requirements",
            objectives=[obj.objective_text for obj in objectives],
            additional_context=" | ".join(additional_context_parts)
            if additional_context_parts
            else None,
            lesson_duration=extracted.get("time_constraints", "45 minutes"),
            class_size=25,  # Default, could be extracted in future
            available_resources=extracted.get("resources", []),
        )

    def _handle_refinement(self, message: str) -> str:
        """Handle lesson refinement requests"""
        # Store the message
        self.lesson_requirements["conversation_context"].append(
            {"role": "user", "message": message, "timestamp": self._get_timestamp()}
        )

        # For now, treat refinement as lesson planning
        # Could be enhanced to specifically modify the generated lesson
        self.set_state("lesson_planning")
        return self._handle_lesson_planning(message)

    def _handle_generation(self, message: str) -> str:
        """Handle generation state"""
        return self._generate_lesson_plan()

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

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

        # Add conversational handlers
        if self.conversational_mode:
            self.add_state_handler(
                "conversational_welcome", self._handle_conversational_welcome
            )
            self.add_state_handler("lesson_planning", self._handle_lesson_planning)
            self.add_state_handler("refinement", self._handle_refinement)
            self.add_state_handler("generation", self._handle_generation)

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
        lesson_plan = self.llm_client.generate_lesson_plan(context, stream=False)
        # Handle the Union[str, Iterator[str]] return type
        final_plan: str
        if isinstance(lesson_plan, str):
            final_plan = lesson_plan
        else:
            # If it's an iterator, join all chunks
            final_plan = "".join(lesson_plan)
        self.lesson_requirements["generated_lesson"] = final_plan
        return final_plan

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

    def chat(self, message: str) -> str:
        """Main chat interface - routes to appropriate state handler"""
        try:
            current_state = self.get_state()
            handler = self.state_handlers.get(current_state)

            if handler:
                return handler(message)
            else:
                # Fallback to lesson planning
                self.set_state("lesson_planning")
                return self._handle_lesson_planning(message)

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase that or try a different approach?"
