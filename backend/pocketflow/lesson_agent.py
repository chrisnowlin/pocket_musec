"""Lesson generation agent for PocketFlow framework"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import json
import re
from backend.pocketflow.agent import Agent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.standards_repository import StandardsRepository
from backend.repositories.models import Standard, Objective, StandardWithObjectives
from backend.llm.chutes_client import ChutesClient, Message, ChutesAuthenticationError
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates
from backend.services.web_search_service import WebSearchService, WebSearchContext
import logging
import asyncio

logger = logging.getLogger(__name__)


class LessonAgent(Agent):
    """Agent for generating music education lessons through conversation"""

    # Thread pool configuration for async operations
    MAX_ASYNC_WORKERS = (
        4  # Limit concurrent async operations to prevent resource exhaustion
    )

    def __init__(
        self,
        flow: Flow,
        store: Store,
        standards_repo: Optional[StandardsRepository] = None,
        llm_client: Optional[ChutesClient] = None,
        conversational_mode: bool = True,
        web_search_enabled: bool = False,
        web_search_service: Optional["WebSearchService"] = None,
    ):
        super().__init__(flow, store, "LessonAgent")
        self.standards_repo = standards_repo or StandardsRepository()
        # Initialize LLM client with graceful fallback
        if llm_client:
            self.llm_client = llm_client
        else:
            try:
                # Try to initialize with API key requirement
                self.llm_client = ChutesClient()
                logger.info("Chutes client initialized successfully")
            except ChutesAuthenticationError:
                # If no API key, initialize without requirement for graceful fallback
                logger.warning(
                    "No CHUTES_API_KEY found - initializing client without authentication"
                )
                self.llm_client = ChutesClient(require_api_key=False)
            except Exception as e:
                logger.error(f"Failed to initialize Chutes client: {e}")
                self.llm_client = ChutesClient(require_api_key=False)
        self.prompt_templates = LessonPromptTemplates()
        self.conversational_mode = conversational_mode
        self.web_search_enabled = web_search_enabled

        # Initialize web search service if enabled
        if self.web_search_enabled and web_search_service is None:
            from backend.services.web_search_service import WebSearchService
            from backend.config import config

            self.web_search_service = WebSearchService(
                api_key=config.web_search.api_key,
                cache_ttl=config.web_search.cache_ttl,
                max_cache_size=config.web_search.max_cache_size,
                timeout=config.web_search.timeout,
                educational_only=config.web_search.educational_only,
                min_relevance_score=config.web_search.min_relevance_score,
            )
        else:
            self.web_search_service = web_search_service
            self.web_search_service = web_search_service

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

    def _normalize_grade_level(self, grade_level: str) -> str:
        """Convert human-readable grade level to database format"""
        if not grade_level:
            return grade_level

        # Map various grade formats to the database format used in new schema
        grade_mapping = {
            "kindergarten": "Kindergarten",
            "k": "Kindergarten",
            "1st grade": "First Grade",
            "first grade": "First Grade",
            "grade 1": "First Grade",
            "1": "First Grade",
            "2nd grade": "Second Grade",
            "second grade": "Second Grade",
            "grade 2": "Second Grade",
            "2": "Second Grade",
            "3rd grade": "Third Grade",
            "third grade": "Third Grade",
            "grade 3": "Third Grade",
            "3": "Third Grade",
            "4th grade": "Fourth Grade",
            "fourth grade": "Fourth Grade",
            "grade 4": "Fourth Grade",
            "4": "Fourth Grade",
            "5th grade": "Fifth Grade",
            "fifth grade": "Fifth Grade",
            "grade 5": "Fifth Grade",
            "5": "Fifth Grade",
            "6th grade": "Sixth Grade",
            "sixth grade": "Sixth Grade",
            "grade 6": "Sixth Grade",
            "6": "Sixth Grade",
            "7th grade": "Grade 7",
            "seventh grade": "Grade 7",
            "grade 7": "Grade 7",
            "7": "Grade 7",
            "8th grade": "Grade 8",
            "eighth grade": "Grade 8",
            "grade 8": "Grade 8",
            "8": "Grade 8",
            # Proficiency levels
            "novice": "Novice",
            "developing": "Developing",
            "intermediate": "Intermediate",
            "accomplished": "Accomplished",
            "advanced": "Advanced",
        }

        normalized = grade_mapping.get(grade_level.lower().strip())
        return normalized if normalized else grade_level

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
                if hasattr(response, "content"):
                    content = response.content
                elif isinstance(response, dict):
                    content = response.get("content", str(response))
                else:
                    content = str(response)

                extracted = json.loads(content)
                return extracted
            except json.JSONDecodeError as e:
                # Get response content for logging
                response_content = str(response)
                logger.warning(f"Failed to parse analysis response: {response_content}")
                logger.error(f"JSON decode error: {e}")
                return {"confidence_score": 0.0}

        except Exception as e:
            logger.error(f"Error analyzing user message: {e}")
            return {"confidence_score": 0.0}

    def _get_relevant_standards(self, extracted_info: Dict[str, Any]) -> List[Standard]:
        """Get relevant standards using semantic search instead of keyword matching"""
        grade_level = extracted_info.get("grade_level")
        musical_topics = extracted_info.get("musical_topics", [])

        if not grade_level:
            logger.warning("No grade level provided for standards search")
            return []

        # Normalize grade level for database compatibility
        normalized_grade = self._normalize_grade_level(grade_level)

        # If no specific topics, get top standards for the grade level
        if not musical_topics:
            try:
                # Use semantic search with a general query for the grade level
                search_results = self.standards_repo.search_standards_semantic(
                    query=f"music education {normalized_grade}",
                    grade_level=normalized_grade,
                    limit=5,
                    similarity_threshold=0.3,  # Lower threshold for broader results
                )
                return [standard for standard, _ in search_results]
            except Exception as e:
                logger.error(f"Error in semantic search for grade-level standards: {e}")
                # Fallback to get standards by grade
                return self.standards_repo.get_standards_by_grade(normalized_grade)[:5]

        # Create search query from musical topics
        search_query = (
            " ".join(musical_topics)
            if musical_topics
            else f"music education {normalized_grade}"
        )

        try:
            # Use semantic search with the musical topics
            search_results = self.standards_repo.search_standards_semantic(
                query=search_query,
                grade_level=normalized_grade,
                limit=5,
                similarity_threshold=0.4,  # Moderate threshold for topic-specific results
            )

            if search_results:
                logger.info(
                    f"Found {len(search_results)} relevant standards using semantic search"
                )
                return [standard for standard, _ in search_results]
            else:
                # Fallback to keyword-based search if no semantic results
                logger.warning(
                    f"No semantic search results found for query: {search_query}"
                )
                return self._fallback_keyword_search(normalized_grade, musical_topics)

        except Exception as e:
            logger.error(f"Error in semantic search for standards: {e}")
            # Fallback to keyword-based search
            return self._fallback_keyword_search(normalized_grade, musical_topics)

    def _fallback_keyword_search(
        self, grade_level: str, musical_topics: List[str]
    ) -> List[Standard]:
        """Fallback method using keyword matching when semantic search fails"""
        try:
            # Get all standards for the grade level
            standards = self.standards_repo.get_standards_by_grade(grade_level)

            if not musical_topics:
                return standards[:5]  # Return first 5 if no specific topics

            # Score standards based on topic relevance using existing keyword logic
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

        except Exception as e:
            logger.error(f"Error in fallback keyword search: {e}")
            return []  # Return empty list if all methods fail

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

    def _get_teaching_strategies_context(
        self, extracted_info: Dict[str, Any]
    ) -> List[str]:
        """
        Retrieve pedagogical content and teaching strategies using semantic search
        from standards and objectives in the database.

        Args:
            extracted_info: Dictionary containing extracted lesson information

        Returns:
            List of teaching strategy context strings
        """
        try:
            grade_level = extracted_info.get("grade_level", "")
            musical_topics = extracted_info.get("musical_topics", [])
            activity_preferences = extracted_info.get("activity_preferences", [])

            # Normalize grade level for database compatibility
            normalized_grade = self._normalize_grade_level(grade_level)

            # Build search query for teaching strategies
            search_terms = []
            if musical_topics:
                search_terms.extend(musical_topics)
            if activity_preferences:
                search_terms.extend(activity_preferences)

            # Add pedagogy-specific terms
            search_terms.extend(
                [
                    "teaching strategies",
                    "pedagogical approaches",
                    "instructional methods",
                    "activities",
                ]
            )

            search_query = (
                " ".join(search_terms)
                if search_terms
                else f"music teaching strategies {grade_level}"
            )

            logger.info(f"Searching for teaching strategies with query: {search_query}")

            # Use semantic search to find relevant standards that contain teaching strategies
            search_results = self.standards_repo.search_standards_semantic(
                query=search_query,
                grade_level=normalized_grade,
                limit=5,
                similarity_threshold=0.3,  # Lower threshold for broader pedagogical results
            )

            # Extract relevant context from the search results
            context_parts = []
            for standard, similarity in search_results:
                # Create context snippet with standard info
                context_part = f"[From Standard: {standard.standard_id} - {standard.strand_name}]\n{standard.standard_text[:300]}..."
                context_parts.append(context_part)

            if context_parts:
                logger.info(
                    f"Retrieved {len(context_parts)} teaching strategy context items"
                )
                return context_parts
            else:
                logger.info("No teaching strategies found in standards")
                return []

        except Exception as e:
            logger.error(f"Error retrieving teaching strategies context: {e}")
            return []

    def _get_assessment_guidance_context(
        self, extracted_info: Dict[str, Any]
    ) -> List[str]:
        """
        Retrieve assessment strategies and guidance using semantic search
        from standards and objectives in the database.

        Args:
            extracted_info: Dictionary containing extracted lesson information

        Returns:
            List of assessment guidance context strings
        """
        try:
            grade_level = extracted_info.get("grade_level", "")
            musical_topics = extracted_info.get("musical_topics", [])

            # Normalize grade level for database compatibility
            normalized_grade = self._normalize_grade_level(grade_level)

            # Build search query for assessment strategies
            search_terms = []
            if musical_topics:
                search_terms.extend(musical_topics)

            # Add assessment-specific terms
            search_terms.extend(
                [
                    "assessment strategies",
                    "evaluation methods",
                    "rubrics",
                    "formative assessment",
                ]
            )

            search_query = (
                " ".join(search_terms)
                if search_terms
                else f"music assessment strategies {normalized_grade}"
            )

            logger.info(f"Searching for assessment guidance with query: {search_query}")

            # Use semantic search to find relevant standards that contain assessment guidance
            search_results = self.standards_repo.search_standards_semantic(
                query=search_query,
                grade_level=normalized_grade,
                limit=5,
                similarity_threshold=0.3,  # Lower threshold for broader assessment results
            )

            # Extract relevant context from the search results
            context_parts = []
            for standard, similarity in search_results:
                # Create context snippet with standard info
                context_part = f"[From Standard: {standard.standard_id} - {standard.strand_name}]\n{standard.standard_text[:300]}..."
                context_parts.append(context_part)

            if context_parts:
                logger.info(
                    f"Retrieved {len(context_parts)} assessment guidance context items"
                )
                return context_parts
            else:
                logger.info("No assessment guidance found in standards")
                return []

        except Exception as e:
            logger.error(f"Error retrieving assessment guidance context: {e}")
            return []

    async def _get_web_search_context(
        self, extracted_info: Dict[str, Any]
    ) -> Tuple[List[str], Optional["WebSearchContext"]]:
        """
        Retrieve web search context for lesson planning using WebSearchService.

        Args:
            extracted_info: Dictionary containing extracted lesson information

        Returns:
            Tuple of (formatted context strings, WebSearchContext object for citations)
        """
        if not self.web_search_enabled or not self.web_search_service:
            logger.debug("Web search not enabled or service not available")
            return [], None

        try:
            grade_level = extracted_info.get("grade_level", "")
            musical_topics = extracted_info.get("musical_topics", [])

            if not musical_topics:
                logger.info("No musical topics provided for web search")
                return [], None

            # Build search query from musical topics
            search_query = " ".join(musical_topics[:3])  # Limit to first 3 topics

            logger.info(f"Searching web for educational resources: {search_query}")

            # Execute web search
            search_context = await self.web_search_service.search_educational_resources(
                query=search_query,
                max_results=5,  # Limit for context
                grade_level=grade_level,
                subject="music",
            )

            if not search_context or not search_context.results:
                logger.info("No web search results found")
                return [], None

            # Store the search context for later citation generation
            self._last_web_search_context = search_context

            # Format results for LLM consumption with citation support
            formatted_context = []
            for result in search_context.results:
                if result.citation_id:  # Check if citation_id exists
                    citation_number = search_context.get_citation_number(
                        result.citation_id
                    )
                    if citation_number:
                        context_item = result.to_context_with_citation(citation_number)
                        formatted_context.append(context_item)
                    else:
                        # Fallback formatting if citation not assigned
                        context_item = (
                            f"[Web Resource - {result.domain}]\n"
                            f"Title: {result.title}\n"
                            f"Content: {result.snippet}\n"
                            f"URL: {result.url}\n"
                            f"Relevance: {result.relevance_score:.2f}"
                        )
                        formatted_context.append(context_item)
                else:
                    # Fallback formatting if citation_id missing
                    context_item = (
                        f"[Web Resource - {result.domain}]\n"
                        f"Title: {result.title}\n"
                        f"Content: {result.snippet}\n"
                        f"URL: {result.url}\n"
                        f"Relevance: {result.relevance_score:.2f}"
                    )
                    formatted_context.append(context_item)

            logger.info(f"Retrieved {len(formatted_context)} web search context items")
            return formatted_context, search_context

        except Exception as e:
            logger.error(f"Error retrieving web search context: {e}")
            # Graceful degradation - return empty list on error
            return [], None

    def _generate_conversational_response_sync(
        self,
        message: str,
        extracted_info: Dict[str, Any],
        relevant_standards: List[Standard],
    ) -> str:
        """Generate a conversational response using Chutes API (sync wrapper)"""
        import time

        start_time = time.time()

        try:
            import asyncio

            # Try to get the current event loop, create new one if none exists
            try:
                loop = asyncio.get_running_loop()
                # Loop is running - we need to run in a thread
                import concurrent.futures

                logger.debug(
                    "Using thread pool for conversational response (event loop running)"
                )
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.MAX_ASYNC_WORKERS
                ) as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._generate_conversational_response(
                            message, extracted_info, relevant_standards
                        ),
                    )
                    result = future.result()
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Conversational response generated in {elapsed:.2f}s (thread pool)"
                    )
                    return result
            except RuntimeError:
                # No running loop - we can use asyncio.run directly
                logger.debug("Using direct asyncio.run for conversational response")
                result = asyncio.run(
                    self._generate_conversational_response(
                        message, extracted_info, relevant_standards
                    )
                )
                elapsed = time.time() - start_time
                logger.info(
                    f"Conversational response generated in {elapsed:.2f}s (direct)"
                )
                return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Error running async conversational response after {elapsed:.2f}s: {e}"
            )
            return f"I understand you're asking about {message}. Let me help you with that!"

    async def _generate_conversational_response(
        self,
        message: str,
        extracted_info: Dict[str, Any],
        relevant_standards: List[Standard],
    ) -> str:
        """Generate a conversational response using Chutes API (async version)"""

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
3. When relevant standards are provided in the context, naturally weave them into your response with their ID, strand, and key details
4. Offer specific, age-appropriate activity ideas or teaching strategies based on the musical topics discussed
5. Be helpful and encouraging, not rigid or form-like
6. If you have enough information, offer to create a lesson plan and tell them to say "generate lesson plan"
7. Keep it conversational and build on what they've told you

FORMATTING REQUIREMENTS:
- Use emojis to make responses engaging and visually appealing (🎵, 🎶, 🥁, 🎹, 🎤, 🎼, ✨, 💡, 🎯, 📚, 🎨, 🌟)
- Use markdown formatting for better readability:
  - Use **bold** for emphasis on key concepts and standard IDs
  - Use *italics* for activity suggestions
  - Use bullet points (• or -) for lists of ideas, standards, or activities
  - Use section headers with ### for organizing information (e.g., "### 🎯 Relevant Standards", "### 🎵 Activity Ideas")
- Keep paragraphs short and easy to read
- Use line breaks to separate ideas
- Make it scannable with clear visual hierarchy
- Include standards naturally in a dedicated section when available
- Include specific activity suggestions based on the musical topics and resources mentioned

Write your response as if you're talking to a fellow music educator. Be warm, knowledgeable, and helpful."""

        messages = [
            Message(role="system", content=self._get_conversational_system_prompt()),
            Message(role="user", content=response_prompt),
        ]

        # Use async wrapper to prevent blocking
        response = await self._async_llm_chat_completion(
            messages=messages, temperature=0.7, max_tokens=800
        )

        # Debug logging to check response type
        logger.debug(f"Generate response type: {type(response)}")

        # Handle both ChatResponse object and dictionary
        # Return the LLM response directly - let it handle all formatting naturally
        if hasattr(response, "content"):
            return response.content
        elif isinstance(response, dict):
            return response.get("content", str(response))
        else:
            return str(response)

    async def _handle_conversational_welcome(self, message: str) -> str:
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

        # Analyze the user's message (async to prevent blocking)
        extracted_info = await self._async_analyze_user_message(message)

        # Update extracted information
        self.lesson_requirements["extracted_info"].update(extracted_info)

        # Get relevant standards
        relevant_standards = self._get_relevant_standards(extracted_info)

        # Store standards for later use
        if relevant_standards:
            self.lesson_requirements["suggested_standards"] = relevant_standards

        # Generate conversational response (async to prevent blocking)
        response = await self._generate_conversational_response(
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
            return self._generate_lesson_plan_sync()

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

        # Generate conversational response (using sync wrapper)
        response = self._generate_conversational_response_sync(
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

    async def _generate_lesson_plan(self) -> str:
        """Generate the actual lesson plan using collected information with RAG and web search context"""
        try:
            # Build lesson context from conversation (now includes RAG and web search context)
            context = await self._build_lesson_context_from_conversation()

            # Log that RAG context is being used
            rag_context = self.lesson_requirements.get("rag_context", {})
            teaching_count = len(rag_context.get("teaching_context", []))
            assessment_count = len(rag_context.get("assessment_context", []))
            web_search_count = len(rag_context.get("web_search_context", []))

            if teaching_count > 0 or assessment_count > 0 or web_search_count > 0:
                logger.info(
                    f"Generating lesson plan with {teaching_count} teaching, {assessment_count} assessment, and {web_search_count} web search context items"
                )

            # Generate the lesson plan with enhanced context (async to prevent blocking)
            lesson_plan = await self._async_llm_generate_lesson_plan(
                context, stream=False
            )

            # Handle the Union[str, Iterator[str]] return type
            final_plan: str
            if isinstance(lesson_plan, str):
                final_plan = lesson_plan
            else:
                # If it's an iterator, join all chunks
                final_plan = "".join(lesson_plan)

            # Add citations section for web search and/or RAG context
            citations_section = ""

            # Web search citations
            if web_search_count > 0:
                # Get the web search context to extract bibliography
                web_search_context_list = rag_context.get("web_search_context", [])
                if web_search_context_list:
                    # Try to get the bibliography from the stored web search service
                    try:
                        if (
                            hasattr(self, "web_search_service")
                            and self.web_search_service
                        ):
                            # Reconstruct the search context from stored context
                            # We need to find the original WebSearchContext object
                            search_context = getattr(
                                self, "_last_web_search_context", None
                            )
                            if search_context and hasattr(
                                search_context, "get_citation_bibliography"
                            ):
                                citations_section = (
                                    search_context.get_citation_bibliography()
                                )
                                if citations_section:
                                    citations_section = f"\n\n{citations_section}\n"
                            else:
                                # Fallback: generate simple citations from context
                                citations_section = self._generate_fallback_citations(
                                    web_search_context_list
                                )
                    except Exception as e:
                        logger.warning(f"Failed to generate citations: {e}")
                        # Fallback citations
                        citations_section = self._generate_fallback_citations(
                            web_search_context_list
                        )

            # RAG citations (teaching strategies and assessment guidance)
            if teaching_count > 0 or assessment_count > 0:
                teaching_context_list = rag_context.get("teaching_context", [])
                assessment_context_list = rag_context.get("assessment_context", [])
                rag_citations = self._generate_rag_citations(
                    teaching_context_list, assessment_context_list
                )
                if rag_citations:
                    # If we already have web search citations, add a separator
                    if citations_section:
                        citations_section += "\n\n---\n"
                    else:
                        citations_section = "\n\n"
                    citations_section += rag_citations

            # Combine lesson plan with citations
            complete_lesson = final_plan + citations_section

            # Store the generated lesson
            self.lesson_requirements["generated_lesson"] = complete_lesson
            # Set to refinement state to allow iteration on the lesson
            self.set_state("refinement")

            # Enhanced response with RAG and web search context information
            context_info = ""
            if teaching_count > 0 or assessment_count > 0 or web_search_count > 0:
                context_parts = []
                if teaching_count > 0:
                    context_parts.append(
                        f"{teaching_count} teaching strategy resources"
                    )
                if assessment_count > 0:
                    context_parts.append(
                        f"{assessment_count} assessment guidance resources"
                    )
                if web_search_count > 0:
                    context_parts.append(f"{web_search_count} current web resources")

                context_info = f"\n\n## 📚 Enhanced with Educational Resources\n\nThis lesson plan was enhanced with {', '.join(context_parts)} retrieved from our knowledge base and current educational web sources."

            response = f"""# 🎉 Your Personalized Music Lesson Plan

---

{complete_lesson}

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
{context_info}
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

    async def _build_lesson_context_from_conversation(self) -> LessonPromptContext:
        """Build lesson context from conversational extraction with structured RAG and web search context"""
        extracted = self.lesson_requirements["extracted_info"]

        # Get the best standard from suggestions OR directly set standard
        standard = None
        objectives = []

        # Priority 1: Use directly set standard from session (e.g., from Browse Standards UI)
        if "standard" in self.lesson_requirements:
            standard = self.lesson_requirements["standard"]
            # Get objectives from directly set objectives OR from standard
            if "objectives" in self.lesson_requirements:
                objectives = self.lesson_requirements["objectives"]
            else:
                objectives = self.standards_repo.get_objectives_for_standard(
                    standard.standard_id
                )
        # Priority 2: Use suggested standards from conversational extraction
        elif "suggested_standards" in self.lesson_requirements:
            standard = self.lesson_requirements["suggested_standards"][0]
            objectives = self.standards_repo.get_objectives_for_standard(
                standard.standard_id
            )

        # Build additional context from conversation (non-RAG)
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

        # RAG Context: Retrieve teaching strategies and assessment guidance
        teaching_context = self._get_teaching_strategies_context(extracted)
        assessment_context = self._get_assessment_guidance_context(extracted)

        # Web Search Context: Retrieve educational resources from web
        (
            web_search_context_list,
            web_search_context_obj,
        ) = await self._get_web_search_context(extracted)

        # Store all context types in lesson requirements for debugging/analysis
        self.lesson_requirements["rag_context"] = {
            "teaching_context": teaching_context,
            "assessment_context": assessment_context,
            "web_search_context": web_search_context_list,
        }

        # Store the WebSearchContext object for citation generation
        if web_search_context_obj:
            self._last_web_search_context = web_search_context_obj

        # Build final additional context (keeping backward compatibility)
        final_additional_context = (
            " | ".join(additional_context_parts) if additional_context_parts else None
        )

        return LessonPromptContext(
            grade_level=self.lesson_requirements.get("grade_level")
            or extracted.get("grade_level", "Grade 3"),
            strand_code=standard.strand_code
            if standard
            else self.lesson_requirements.get("strand_code", "Create"),
            strand_name=standard.strand_name if standard else "Create Strand",
            strand_description=standard.strand_description
            if standard
            else "Creating and expressing music",
            standard_id=standard.standard_id if standard else "Custom Lesson",
            standard_text=standard.standard_text
            if standard
            else "Custom lesson based on teacher requirements",
            objectives=[obj.objective_text for obj in objectives],
            additional_context=final_additional_context,
            lesson_duration=self.lesson_requirements.get("lesson_duration")
            or extracted.get("time_constraints", "45 minutes"),
            class_size=self.lesson_requirements.get("class_size")
            or 25,  # Use session value or default
            available_resources=extracted.get("resources", []),
            # NEW: Structured RAG context fields
            teaching_context=teaching_context,
            assessment_context=assessment_context,
            web_search_context=web_search_context_list,
        )

    def _generate_lesson_plan_sync(self) -> str:
        """Generate the actual lesson plan using collected information with RAG and web search context (sync version)"""
        import time

        start_time = time.time()

        try:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                # Loop is running - use thread pool
                import concurrent.futures

                logger.debug(
                    "Using thread pool for lesson plan generation (event loop running)"
                )
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.MAX_ASYNC_WORKERS
                ) as executor:
                    future = executor.submit(asyncio.run, self._generate_lesson_plan())
                    result = future.result()
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Lesson plan generated in {elapsed:.2f}s (thread pool)"
                    )
                    return result
            except RuntimeError:
                # No running loop - use asyncio.run directly
                logger.debug("Using direct asyncio.run for lesson plan generation")
                result = asyncio.run(self._generate_lesson_plan())
                elapsed = time.time() - start_time
                logger.info(f"Lesson plan generated in {elapsed:.2f}s (direct)")
                return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Error running async lesson generation after {elapsed:.2f}s: {e}"
            )
            return self._generate_fallback_lesson()

    def _generate_fallback_lesson(self) -> str:
        """Generate a fallback lesson when async fails"""
        return """# 🎵 Basic Music Lesson Plan

## 🎯 Learning Objectives
- Students will explore basic musical concepts
- Students will participate in musical activities

## 🎵 Activities
1. **Warm-up**: Simple rhythm exercises
2. **Main Activity**: Basic music exploration
3. **Cool-down**: Reflective listening

## 📝 Assessment
- Observe student participation
- Check for understanding of basic concepts

## 🎨 Extensions
- Try different instruments
- Explore various musical styles

---

*This is a basic fallback lesson plan. Please try again for a more personalized lesson.*"""

    def _handle_refinement(self, message: str) -> str:
        """Handle lesson refinement requests"""
        # Store the message
        self.lesson_requirements["conversation_context"].append(
            {"role": "user", "message": message, "timestamp": self._get_timestamp()}
        )

        # Check if user wants to generate a new lesson from scratch
        if self._should_generate_lesson(message):
            # User wants to regenerate with refinements
            self.set_state("lesson_planning")
            return self._handle_lesson_planning(message)

        # Otherwise, use LLM to refine the existing lesson
        try:
            # Get the current lesson
            current_lesson = self.lesson_requirements.get("generated_lesson", "")

            if not current_lesson:
                # No lesson to refine, treat as new generation
                self.set_state("lesson_planning")
                return self._handle_lesson_planning(message)

            # Create refinement prompt for LLM
            refinement_prompt = f"""You are refining a music lesson plan based on teacher feedback.

Current Lesson Plan:
{current_lesson}

Teacher's Refinement Request:
{message}

Please provide the refined lesson plan incorporating the teacher's feedback. Maintain the same structure and format as the original lesson, but make the requested changes. If the request is unclear, make reasonable improvements based on best practices.

Refined Lesson Plan:"""

            # Use LLM to refine the lesson
            if (
                self.llm_client
                and hasattr(self.llm_client, "is_available")
                and self.llm_client.is_available()
            ):
                from backend.llm.chutes_client import Message

                messages = [
                    Message(
                        role="system",
                        content="You are a music education specialist helping teachers refine lesson plans.",
                    ),
                    Message(role="user", content=refinement_prompt),
                ]

                # Use the lesson plan token limit for refinements too
                response = self.llm_client.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=6000,  # Use same high limit as lesson generation
                )

                refined_lesson = response.content.strip()

                # Update stored lesson
                self.lesson_requirements["generated_lesson"] = refined_lesson

                # Build response
                refinement_response = f"""# ✨ Lesson Plan Updated!

---

{refined_lesson}

---

## 💬 Continue Refining

I've updated your lesson plan based on your feedback! Would you like to make any other adjustments?

**You can:**
• Modify specific sections (timing, activities, assessment, etc.)
• Add or remove content
• Adjust for different needs or contexts
• Generate a completely new lesson with "generate lesson plan"

Just let me know what you'd like to change! 🎵"""

                self.lesson_requirements["conversation_context"].append(
                    {
                        "role": "assistant",
                        "message": refinement_response,
                        "timestamp": self._get_timestamp(),
                    }
                )

                return refinement_response
            else:
                # Fallback if LLM not available
                return "I'd love to help refine your lesson, but I need an LLM connection to make those changes. Please try again later or describe what you'd like changed and I'll help you plan it out."

        except Exception as e:
            logger.error(f"Error in refinement handler: {e}")
            # Fallback to lesson planning mode
            self.set_state("lesson_planning")
            return self._handle_lesson_planning(message)

    def _handle_generation_sync(self, message: str) -> str:
        """Handle generation state (sync wrapper)"""
        import time

        start_time = time.time()

        try:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                # Loop is running - use thread pool
                import concurrent.futures

                logger.debug(
                    "Using thread pool for generation handler (event loop running)"
                )
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.MAX_ASYNC_WORKERS
                ) as executor:
                    future = executor.submit(asyncio.run, self._generate_lesson_plan())
                    result = future.result()
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Generation handler completed in {elapsed:.2f}s (thread pool)"
                    )
                    return result
            except RuntimeError:
                # No running loop - use asyncio.run directly
                logger.debug("Using direct asyncio.run for generation handler")
                result = asyncio.run(self._generate_lesson_plan())
                elapsed = time.time() - start_time
                logger.info(f"Generation handler completed in {elapsed:.2f}s (direct)")
                return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error in generation handler after {elapsed:.2f}s: {e}")
            return self._generate_fallback_lesson()

    def _handle_conversational_welcome_sync(self, message: str) -> str:
        """Handle the initial conversational exchange (sync wrapper)"""
        import time

        start_time = time.time()

        try:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                # Loop is running - use thread pool
                import concurrent.futures

                logger.debug(
                    "Using thread pool for conversational welcome (event loop running)"
                )
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.MAX_ASYNC_WORKERS
                ) as executor:
                    future = executor.submit(
                        asyncio.run, self._handle_conversational_welcome(message)
                    )
                    result = future.result()
                    elapsed = time.time() - start_time
                    logger.info(
                        f"Conversational welcome completed in {elapsed:.2f}s (thread pool)"
                    )
                    return result
            except RuntimeError:
                # No running loop - use asyncio.run directly
                logger.debug("Using direct asyncio.run for conversational welcome")
                result = asyncio.run(self._handle_conversational_welcome(message))
                elapsed = time.time() - start_time
                logger.info(
                    f"Conversational welcome completed in {elapsed:.2f}s (direct)"
                )
                return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Error running async conversational welcome after {elapsed:.2f}s: {e}"
            )
            return self._generate_fallback_welcome(message)

    def _generate_fallback_welcome(self, message: str) -> str:
        """Generate a fallback welcome when async fails"""
        return f"""# 🎵 Welcome to PocketMusec Lesson Planning!

Hello! I'm your AI music education assistant. I see you're interested in: "{message}"

I'm here to help you create engaging, standards-aligned music lessons! 

To get started, could you tell me:
- What grade level are you teaching?
- What musical topic or concept would you like to focus on?
- How much time do you have for the lesson?

Feel free to share any other details about your students or available resources! 🎶"""

    def _generate_fallback_citations(self, web_search_context: List[str]) -> str:
        """Generate fallback citations from web search context strings"""
        try:
            citations = ["## 📚 Web Sources References\n"]

            for i, context_item in enumerate(web_search_context, 1):
                # Extract URL from context item if possible
                lines = context_item.split("\n")
                url = ""
                title = ""
                domain = ""

                for line in lines:
                    if line.startswith("URL: "):
                        url = line.replace("URL: ", "").strip()
                    elif line.startswith("Title: "):
                        title = line.replace("Title: ", "").strip()
                    elif line.startswith("[Web Source: "):
                        # Extract domain from the header
                        header = line.split(" - ")[1] if " - " in line else ""
                        domain = header.replace("]", "").strip()

                # Create citation
                if title and url:
                    citation = f"[{i}] {title}"
                    if domain:
                        citation += f", {domain}"
                    citation += f", {url}."
                    citations.append(citation)

            return "\n".join(citations) if len(citations) > 1 else ""

        except Exception as e:
            logger.warning(f"Failed to generate fallback citations: {e}")
            return ""

    def _generate_rag_citations(
        self, teaching_context: List[str], assessment_context: List[str]
    ) -> str:
        """Generate citations for RAG context (teaching strategies and assessment guidance)"""
        try:
            if not teaching_context and not assessment_context:
                return ""

            citations = ["## 📚 Educational Resources References\n"]
            citation_num = 1

            # Add teaching strategy citations
            if teaching_context:
                citations.append("\n**Teaching Strategies:**")
                for context_item in teaching_context:
                    # Extract source information if available
                    # For now, use generic NC Music Standards reference
                    citations.append(
                        f"[{citation_num}] North Carolina Department of Public Instruction. (2023). "
                        f"Arts Education Standard Course of Study: Music - Teaching Strategies and Pedagogical Approaches. "
                        f"Retrieved from NC Music Standards Database."
                    )
                    citation_num += 1

            # Add assessment citations
            if assessment_context:
                citations.append("\n**Assessment Guidance:**")
                for context_item in assessment_context:
                    citations.append(
                        f"[{citation_num}] North Carolina Department of Public Instruction. (2023). "
                        f"Arts Education Standard Course of Study: Music - Assessment and Evaluation Strategies. "
                        f"Retrieved from NC Music Standards Database."
                    )
                    citation_num += 1

            return "\n".join(citations) if len(citations) > 1 else ""

        except Exception as e:
            logger.warning(f"Failed to generate RAG citations: {e}")
            return ""

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
                "conversational_welcome", self._handle_conversational_welcome_sync
            )
            self.add_state_handler("lesson_planning", self._handle_lesson_planning)
            self.add_state_handler("refinement", self._handle_refinement)
            self.add_state_handler("generation", self._handle_generation_sync)

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
        """Build context dictionary for lesson generation with RAG context support"""
        objective_texts = [
            obj.objective_text
            for obj in self.lesson_requirements.get("selected_objectives", [])
        ]

        # Extract basic info for RAG context retrieval
        extracted_info = {
            "grade_level": self.lesson_requirements["grade_level"],
            "musical_topics": [
                self.lesson_requirements["standard"].standard_text[:100]
            ],  # Use standard as topic
        }

        # RAG Context: Retrieve teaching strategies and assessment guidance
        teaching_context = self._get_teaching_strategies_context(extracted_info)
        assessment_context = self._get_assessment_guidance_context(extracted_info)

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
            lesson_duration=self.lesson_requirements.get("lesson_duration")
            or self.lesson_requirements.get("time_constraints"),
            class_size=self.lesson_requirements.get("class_size") or 25,
            available_resources=self.lesson_requirements.get("available_resources", []),
            # NEW: Structured RAG context fields
            teaching_context=teaching_context,
            assessment_context=assessment_context,
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
                # Serialize standard object or pass through if already a dict
                if value:
                    if isinstance(value, dict):
                        # Already serialized
                        serializable_reqs[key] = value
                    else:
                        # Serialize standard object
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
            elif key == "objectives":
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
            elif key == "suggested_standards":
                # Serialize standards list
                if value:
                    serializable_reqs[key] = [
                        {
                            "standard_id": std.standard_id,
                            "grade_level": std.grade_level,
                            "strand_code": std.strand_code,
                            "strand_name": std.strand_name,
                            "standard_text": std.standard_text,
                            "strand_description": std.strand_description,
                        }
                        for std in value
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
                # Handle both old format (standard_id) and new format (id from StandardResponse)
                standard_id = (
                    value.get("standard_id") or value.get("id") or value.get("code")
                )
                standard_text = value.get("standard_text") or value.get("title")
                strand_description = value.get("strand_description") or value.get(
                    "description"
                )

                self.lesson_requirements[key] = Standard(
                    standard_id=standard_id,
                    grade_level=value["grade_level"],
                    strand_code=value["strand_code"],
                    strand_name=value["strand_name"],
                    standard_text=standard_text,
                    strand_description=strand_description,
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
            elif key == "objectives" and value:
                # Reconstruct Objective objects
                self.lesson_requirements[key] = [
                    Objective(
                        objective_id=obj["objective_id"],
                        standard_id=obj["standard_id"],
                        objective_text=obj["objective_text"],
                    )
                    for obj in value
                ]
            elif key == "suggested_standards" and value:
                # Reconstruct Standard objects
                self.lesson_requirements[key] = [
                    Standard(
                        standard_id=std["standard_id"],
                        grade_level=std["grade_level"],
                        strand_code=std["strand_code"],
                        strand_name=std["strand_name"],
                        standard_text=std["standard_text"],
                        strand_description=std["strand_description"],
                    )
                    for std in value
                ]
            else:
                self.lesson_requirements[key] = value

        # Restore conversation history
        history = state.get("conversation_history", [])
        self.conversation_history = history

    def chat(self, message: str) -> str:
        """Main chat interface - routes to appropriate state handler"""
        try:
            # Store user message in conversation history
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": message,
                    "state": self.current_state,
                    "timestamp": self._get_timestamp(),
                }
            )

            current_state = self.get_state()
            handler = self.state_handlers.get(current_state)

            if handler:
                response = handler(message)
            else:
                # Fallback to lesson planning
                self.set_state("lesson_planning")
                response = self._handle_lesson_planning(message)

            # Store assistant response in conversation history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "state": self.current_state,
                    "timestamp": self._get_timestamp(),
                }
            )

            return response

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            error_response = f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase that or try a different approach?"

            # Store error response in history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": error_response,
                    "state": self.current_state,
                    "timestamp": self._get_timestamp(),
                }
            )

            return error_response

    # Async wrapper methods for non-blocking LLM calls

    async def _async_llm_chat_completion(
        self, messages, temperature=0.7, max_tokens=2000
    ):
        """Async wrapper for LLM chat completion to prevent blocking"""
        import time
        from types import SimpleNamespace

        start_time = time.time()

        if (
            not self.llm_client
            or not hasattr(self.llm_client, "is_available")
            or not self.llm_client.is_available()
        ):
            logger.debug("LLM client unavailable, returning fallback response")
            # Return a simple object with a content attribute for consistency
            return SimpleNamespace(
                content="I'm unable to process your request right now as no LLM service is configured."
            )

        # Run the blocking LLM call in a separate thread
        logger.debug(
            f"Starting async LLM chat completion (temp={temperature}, max_tokens={max_tokens})"
        )
        result = await asyncio.to_thread(
            self.llm_client.chat_completion,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = time.time() - start_time
        logger.info(f"LLM chat completion took {elapsed:.2f}s")
        return result

    async def _async_llm_generate_lesson_plan(self, context, stream=False):
        """Async wrapper for LLM lesson plan generation to prevent blocking"""
        import time

        start_time = time.time()

        if (
            not self.llm_client
            or not hasattr(self.llm_client, "is_available")
            or not self.llm_client.is_available()
        ):
            logger.debug("LLM client unavailable for lesson plan generation")
            return "I'm unable to generate the lesson plan right now as no LLM service is configured."

        # Run the blocking LLM call in a separate thread
        logger.debug(f"Starting async lesson plan generation (stream={stream})")
        result = await asyncio.to_thread(
            self.llm_client.generate_lesson_plan, context=context, stream=stream
        )
        elapsed = time.time() - start_time
        logger.info(f"LLM lesson plan generation took {elapsed:.2f}s")
        return result

    async def _async_analyze_user_message(self, message: str) -> Dict[str, Any]:
        """Async version of _analyze_user_message to prevent blocking"""
        try:
            analysis_prompt = f"""Analyze this music teacher's message and extract key information for lesson planning:

Message: "{message}"

Extract and return ONLY a JSON object with these exact keys:
- grade_level: Elementary, Middle, or High school
- topic: Main musical topic or concept
- duration: Lesson duration in minutes (estimate if not specified)
- objectives: List of 2-4 learning objectives based on the message

Keep responses concise and focused on music education."""

            messages = [
                Message(
                    role="system", content=self._get_conversational_system_prompt()
                ),
                Message(role="user", content=analysis_prompt),
            ]

            # Use async wrapper
            response = await self._async_llm_chat_completion(
                messages=messages, temperature=0.3, max_tokens=500
            )

            # Parse the response
            import json

            try:
                # Handle ChatResponse object
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Try to extract JSON from the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    extracted_info = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    extracted_info = {
                        "grade_level": "Elementary",
                        "topic": "General music",
                        "duration": "30 minutes",
                        "objectives": ["General music exploration"],
                    }

                # Ensure required keys exist
                default_info = {
                    "grade_level": "Elementary",
                    "topic": "General music",
                    "duration": "30 minutes",
                    "objectives": ["General music exploration"],
                }

                for key in default_info:
                    if key not in extracted_info:
                        extracted_info[key] = default_info[key]

                return extracted_info

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                return {
                    "grade_level": "Elementary",
                    "topic": "General music",
                    "duration": "30 minutes",
                    "objectives": ["General music exploration"],
                    "error": "parsing_error",
                }

        except Exception as e:
            logger.error(f"Error in async message analysis: {e}")
            return {
                "grade_level": "Elementary",
                "topic": "General music",
                "duration": "30 minutes",
                "objectives": ["General music exploration"],
                "error": "analysis_error",
            }
