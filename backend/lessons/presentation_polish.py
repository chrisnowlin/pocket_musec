"""Optional LLM polish service for presentation slides.

This module provides functions to optionally enhance slide content using
the Chutes LLM service, with graceful fallback to scaffold content.
"""

import json
import logging
from typing import List, Optional, Dict, Any
import time

from backend.llm.chutes_client import ChutesClient, Message, ChutesAPIError
from .presentation_schema import PresentationSlide, PresentationDocument
from .presentation_builder import build_presentation_scaffold
from .schema_m2 import LessonDocumentM2

logger = logging.getLogger(__name__)


class PresentationPolishService:
    """Service for polishing presentation slides using LLM."""

    def __init__(self, chutes_client: Optional[ChutesClient] = None):
        self.chutes_client = chutes_client or ChutesClient(require_api_key=False)
        self.timeout_seconds = 30
        self.max_retries = 2

    def is_available(self) -> bool:
        """Check if LLM polish service is available."""
        return self.chutes_client.is_available()

    def polish_slides(
        self,
        lesson: LessonDocumentM2,
        scaffold_slides: List[PresentationSlide],
        timeout_seconds: Optional[int] = None,
    ) -> List[PresentationSlide]:
        """Polish scaffold slides using LLM, with fallback to original.

        Args:
            lesson: The original lesson document
            scaffold_slides: The deterministic scaffold slides
            timeout_seconds: Maximum time to wait for LLM response

        Returns:
            Polished slides if successful, otherwise original scaffold slides
        """
        if not self.is_available():
            logger.info("LLM service not available, using scaffold slides")
            return scaffold_slides

        timeout = timeout_seconds or self.timeout_seconds

        try:
            return self._polish_with_llm(lesson, scaffold_slides, timeout)
        except Exception as e:
            logger.warning(f"LLM polish failed, using scaffold slides: {e}")
            return scaffold_slides

    def _polish_with_llm(
        self,
        lesson: LessonDocumentM2,
        scaffold_slides: List[PresentationSlide],
        timeout_seconds: int,
    ) -> List[PresentationSlide]:
        """Attempt to polish slides using LLM with timeout."""

        # Prepare the prompt with slide schema and requirements
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(lesson, scaffold_slides)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        # Add JSON mode constraint for structured output
        for attempt in range(self.max_retries):
            try:
                response = self.chutes_client.chat_completion(
                    messages=messages,
                    temperature=0.3,  # Lower temperature for consistent output
                    max_tokens=4000,  # Sufficient for slide content
                    timeout=timeout_seconds,
                    # Note: Add response_format={"type": "json_object"} if supported
                )

                # Parse and validate the response
                polished_slides = self._parse_llm_response(
                    response.content, scaffold_slides
                )

                if polished_slides:
                    logger.info(f"Successfully polished {len(polished_slides)} slides")
                    return polished_slides
                else:
                    logger.warning("LLM returned empty or invalid slides")

            except ChutesAPIError as e:
                logger.warning(f"LLM API error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)

        # If we get here, all attempts failed
        raise Exception("Failed to polish slides after multiple attempts")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for slide polishing."""
        return """You are an expert music education curriculum designer. Your task is to refine presentation slides for teachers while maintaining educational accuracy and clarity.

CRITICAL REQUIREMENTS:
1. You MUST respond with valid JSON only - no explanations or text outside the JSON
2. NEVER add new learning objectives or change the educational content
3. Maintain all NC standards references exactly as provided
4. Keep teacher scripts concise (under 80 words) and practical
5. Limit each slide to 3-5 concise bullet points
6. Use clear, teacher-friendly language appropriate for music education

SLIDE SCHEMA:
Each slide must follow this exact structure:
{
  "slides": [
    {
      "id": "slide_id",
      "title": "Slide Title",
      "subtitle": "Optional subtitle",
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "teacher_script": "Concise script under 80 words",
      "visual_prompt": "Optional visual suggestion",
      "duration_minutes": 10,
      "source_section": "overview|objectives|materials|warmup|activity|assessment|differentiation|closure",
      "activity_id": "optional_activity_id",
      "standard_codes": ["MH.M.NP.1", "MH.M.CR.1"]
    }
  ]
}

Focus on making content more engaging and actionable for teachers while preserving all educational standards and objectives."""

    def _build_user_prompt(
        self,
        lesson: LessonDocumentM2,
        scaffold_slides: List[PresentationSlide],
    ) -> str:
        """Build the user prompt with lesson context and scaffold slides."""

        # Build lesson context
        lesson_context = {
            "title": lesson.title,
            "grade": lesson.grade,
            "strands": lesson.strands,
            "objectives": lesson.objectives,
            "total_duration": lesson.content.timing.total_minutes,
            "standards_count": len(lesson.standards),
        }

        # Convert scaffold slides to JSON for the prompt
        scaffold_data = []
        for slide in scaffold_slides:
            slide_dict = {
                "id": slide.id,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "key_points": slide.key_points,
                "teacher_script": slide.teacher_script,
                "visual_prompt": slide.visual_prompt,
                "duration_minutes": slide.duration_minutes,
                "source_section": slide.source_section.value,
                "activity_id": slide.activity_id,
                "standard_codes": slide.standard_codes,
            }
            scaffold_data.append(slide_dict)

        prompt = f"""Please refine these presentation slides for a music lesson. 

LESSON CONTEXT:
{json.dumps(lesson_context, indent=2)}

CURRENT SLIDES:
{json.dumps(scaffold_data, indent=2)}

TASK:
Refine the slides to be more engaging and actionable for teachers while:
- Preserving all learning objectives and NC standards
- Keeping teacher scripts practical and under 80 words
- Ensuring 3-5 concise bullet points per slide
- Using clear, music-education appropriate language
- Maintaining the exact same slide structure and order

Respond with ONLY the JSON array of polished slides following the schema provided in the system prompt."""

        return prompt

    def _parse_llm_response(
        self,
        response_content: str,
        original_slides: List[PresentationSlide],
    ) -> List[PresentationSlide]:
        """Parse and validate LLM response into PresentationSlide objects."""
        try:
            # Try to extract JSON from the response
            response_content = response_content.strip()

            # Remove any markdown code blocks
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            if response_content.startswith("```"):
                response_content = response_content[3:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            response_content = response_content.strip()

            # Parse JSON
            data = json.loads(response_content)

            if not isinstance(data, dict) or "slides" not in data:
                logger.error("Invalid response structure: missing 'slides' field")
                return []

            slides_data = data["slides"]
            if not isinstance(slides_data, list):
                logger.error("Invalid response structure: 'slides' is not a list")
                return []

            # Validate and convert slides
            polished_slides = []
            for i, slide_data in enumerate(slides_data):
                try:
                    # Validate required fields
                    if not all(
                        key in slide_data
                        for key in [
                            "id",
                            "title",
                            "key_points",
                            "teacher_script",
                            "source_section",
                        ]
                    ):
                        logger.warning(f"Slide {i} missing required fields, skipping")
                        continue

                    # Convert source_section string to enum
                    if isinstance(slide_data["source_section"], str):
                        try:
                            source_section = slide_data["source_section"]
                            # Keep as string, will be converted in PresentationSlide constructor
                        except ValueError:
                            logger.warning(
                                f"Invalid source_section in slide {i}, using original"
                            )
                            source_section = original_slides[i].source_section.value
                    else:
                        source_section = original_slides[i].source_section.value

                    # Create polished slide
                    polished_slide = PresentationSlide(
                        id=slide_data.get("id", original_slides[i].id),
                        title=slide_data.get("title", original_slides[i].title),
                        subtitle=slide_data.get("subtitle"),
                        key_points=slide_data.get(
                            "key_points", original_slides[i].key_points
                        ),
                        teacher_script=slide_data.get(
                            "teacher_script", original_slides[i].teacher_script
                        ),
                        visual_prompt=slide_data.get("visual_prompt"),
                        duration_minutes=slide_data.get("duration_minutes"),
                        source_section=source_section,
                        activity_id=slide_data.get("activity_id"),
                        standard_codes=slide_data.get(
                            "standard_codes", original_slides[i].standard_codes
                        ),
                    )
                    polished_slides.append(polished_slide)

                except Exception as e:
                    logger.warning(f"Failed to parse slide {i}: {e}")
                    # Use original slide as fallback
                    if i < len(original_slides):
                        polished_slides.append(original_slides[i])

            # Ensure we have the same number of slides
            while len(polished_slides) < len(original_slides):
                polished_slides.append(original_slides[len(polished_slides)])

            return polished_slides

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return []


def polish_presentation_slides(
    lesson: LessonDocumentM2,
    scaffold_slides: List[PresentationSlide],
    chutes_client: Optional[ChutesClient] = None,
    timeout_seconds: int = 30,
) -> List[PresentationSlide]:
    """Convenience function to polish presentation slides.

    Args:
        lesson: The original lesson document
        scaffold_slides: The scaffold slides to polish
        chutes_client: Optional Chutes client instance
        timeout_seconds: Maximum time to wait for LLM

    Returns:
        Polished slides if successful, otherwise original scaffold slides
    """
    polish_service = PresentationPolishService(chutes_client)
    return polish_service.polish_slides(lesson, scaffold_slides, timeout_seconds)
