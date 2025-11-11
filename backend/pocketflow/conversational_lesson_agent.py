"""Conversational lesson generation agent for PocketFlow framework

This agent uses the Chutes API to understand user intent, extract information,
and provide intelligent suggestions rather than following a rigid form-based approach.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from backend.pocketflow.agent import Agent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.models import Standard, Objective, StandardWithObjectives
from backend.llm.chutes_client import ChutesClient, Message
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates
import logging

logger = logging.getLogger(__name__)


class ConversationalLessonAgent(Agent):
    """Intelligent conversational agent for music education lesson planning"""

    def __init__(
        self,
        flow: Flow,
        store: Store,
        standards_repo: Optional[StandardsRepository] = None,
        llm_client: Optional[ChutesClient] = None,
    ):
        super().__init__(flow, store, "ConversationalLessonAgent")
        self.standards_repo = standards_repo or StandardsRepository()
        self.llm_client = llm_client or ChutesClient()
        self.prompt_templates = LessonPromptTemplates()

        # Initialize lesson requirements with conversational context
        self.lesson_requirements: Dict[str, Any] = {
            "conversation_context": [],
            "extracted_info": {},
            "suggestions_made": [],
            "user_preferences": {},
            "current_focus": None,
        }

        # Set up simplified state handlers
        self._setup_state_handlers()

        # Start with conversational welcome
        self.set_state("conversational_welcome")

    def _setup_state_handlers(self) -> None:
        """Set up handlers for conversational flow"""
        self.add_state_handler(
            "conversational_welcome", self._handle_conversational_welcome
        )
        self.add_state_handler("lesson_planning", self._handle_lesson_planning)
        self.add_state_handler("refinement", self._handle_refinement)
        self.add_state_handler("generation", self._handle_generation)
        self.add_state_handler("complete", self._handle_complete)

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
</information_extraction>

<suggestions_and_guidance>
- Suggest relevant standards based on lesson ideas
- Recommend age-appropriate activities and materials
- Provide assessment strategies and differentiation ideas
- Offer cross-curricular connections when relevant
- Share best practices for music education
- Help teachers refine and develop their initial ideas
</suggestions_and_guidance>"""

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

            # Parse the JSON response
            try:
                extracted = json.loads(response.content)
                return extracted
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse analysis response: {response.content}")
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

Write your response as if you're talking to a fellow music educator. Be warm, knowledgeable, and helpful."""

        messages = [
            Message(role="system", content=self._get_conversational_system_prompt()),
            Message(role="user", content=response_prompt),
        ]

        response = self.llm_client.chat_completion(
            messages=messages, temperature=0.7, max_tokens=800
        )

        return response.content

    def _handle_conversational_welcome(self, message: str) -> str:
        """Handle the initial conversational exchange"""
        # Store the message in conversation context
        self.lesson_requirements["conversation_context"].append(
            {"role": "user", "message": message, "timestamp": self._get_timestamp()}
        )

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

        # Store the response
        self.lesson_requirements["conversation_context"].append(
            {
                "role": "assistant",
                "message": response,
                "timestamp": self._get_timestamp(),
            }
        )

        # Move to lesson planning state
        self.set_state("lesson_planning")

        return response

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
            lesson_plan = self.llm_client.generate_lesson_plan(context)

            # Store the generated lesson
            self.lesson_requirements["generated_lesson"] = lesson_plan
            self.set_state("complete")

            response = f"""🎉 Here's your personalized lesson plan based on our conversation!

{lesson_plan}

---

This lesson plan was created specifically for you based on what you shared. Feel free to ask me to:
- Adjust any activities or timing
- Add differentiation strategies
- Include assessment ideas
- Modify for different resources
- Create cross-curricular connections

What would you like to refine about this lesson?"""

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

    def _handle_complete(self, message: str) -> str:
        """Handle completion state"""
        if message.lower() in ["new lesson", "start over", "another lesson"]:
            self.reset_conversation()
            return self._handle_conversational_welcome(message)

        # Continue conversation for refinements
        self.set_state("lesson_planning")
        return self._handle_lesson_planning(message)

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

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

    def get_lesson_requirements(self) -> Dict[str, Any]:
        """Get the collected lesson requirements"""
        return self.lesson_requirements.copy()

    def get_generated_lesson(self) -> Optional[str]:
        """Get the generated lesson plan"""
        return self.lesson_requirements.get("generated_lesson")

    def reset_conversation(self) -> None:
        """Reset the conversation for a new lesson"""
        self.lesson_requirements = {
            "conversation_context": [],
            "extracted_info": {},
            "suggestions_made": [],
            "user_preferences": {},
            "current_focus": None,
        }
        self.clear_history()
        self.set_state("conversational_welcome")

    def serialize_state(self) -> str:
        """Serialize agent state to JSON for persistence"""
        state = {
            "current_state": self.get_state(),
            "lesson_requirements": self.lesson_requirements,
            "conversation_history": self.get_conversation_history(),
        }
        return json.dumps(state)

    def restore_state(self, state_json: str) -> None:
        """Restore agent state from JSON"""
        state = json.loads(state_json)

        # Restore current state
        self.set_state(state.get("current_state", "conversational_welcome"))

        # Restore lesson requirements
        self.lesson_requirements = state.get(
            "lesson_requirements",
            {
                "conversation_context": [],
                "extracted_info": {},
                "suggestions_made": [],
                "user_preferences": {},
                "current_focus": None,
            },
        )

        # Restore conversation history
        history = state.get("conversation_history", [])
        self.conversation_history = history
