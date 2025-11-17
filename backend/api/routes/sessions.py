"""Lesson session and chat endpoints"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.repositories.session_repository import SessionRepository
from backend.repositories.lesson_repository import LessonRepository
from backend.repositories.standards_repository import StandardsRepository
from backend.pocketflow.lesson_agent import LessonAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.utils.standards import format_grade_display, format_grade_for_storage
from backend.llm.model_router import ModelRouter
from backend.config import config
from backend.models.streaming_schema import (
    StreamingEvent,
    create_delta_event,
    create_status_event,
    create_persisted_event,
    create_complete_event,
    create_error_event,
    emit_stream_event
)
from ..models import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    ChatMessageRequest,
    ChatResponse,
    LessonSummary,
    StandardResponse,
    ModelSelectionRequest,
    ModelAvailabilityResponse,
)
from ..dependencies import get_current_user
from backend.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _manual_normalize_standards(session, repo: StandardsRepository):
    """Fallback manual normalization for standards"""
    selected_standards_resp = []

    # Import the grade formatting utility
    from backend.utils.standards import format_grade_display, format_grade_for_storage

    # Handle comma-separated standards
    if session.selected_standards:
        standards_list = [
            standard.strip()
            for standard in session.selected_standards.split(',')
            if standard.strip()
        ]

        for standard_id in standards_list:
            standard = repo.get_standard_by_id(standard_id)
            if standard:
                # Convert database grade format to frontend display format
                grade_display = format_grade_display(standard.grade_level) or "Unknown Grade"

                # Get objectives for this standard
                objectives = repo.get_objectives_for_standard(standard.standard_id)
                # Include objective codes in the format "code - text" to match standards display
                learning_objectives = [
                    f"{obj.objective_id} - {obj.objective_text}" for obj in objectives
                ][:3]

                standard_response = {
                    "id": standard.standard_id,
                    "code": standard.standard_id,
                    "grade": grade_display,  # Use formatted grade display
                    "strandCode": standard.strand_code,
                    "strandName": standard.strand_name,
                    "title": standard.standard_text,
                    "description": standard.standard_text,
                    "objectives": len(objectives),
                    "learningObjectives": learning_objectives,
                }
                selected_standards_resp.append(standard_response)

    return selected_standards_resp


def _session_to_response(session, repo: StandardsRepository, session_repo: SessionRepository = None) -> SessionResponse:
    """Convert session database model to API response with field normalization"""

    # Use repository helpers for field normalization if available
    if session_repo:
        selected_standards_resp = session_repo.normalize_standards_for_response(session, repo)
        selected_objectives_resp = session_repo.normalize_objectives_for_response(session)
    else:
        # Fallback to manual parsing for backward compatibility
        selected_standards_resp = _manual_normalize_standards(session, repo)
        selected_objectives_resp = _manual_normalize_objectives(session)

    return SessionResponse(
        id=session.id,
        grade_level=format_grade_display(session.grade_level) or "Unknown Grade",
        strand_code=session.strand_code,
        selected_standards=selected_standards_resp,
        selected_objectives=selected_objectives_resp,
        selected_model=getattr(session, "selected_model", None),
        additional_context=session.additional_context,
        conversation_history=session.conversation_history,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _manual_normalize_objectives(session):
    """Fallback manual normalization for objectives"""
    if not session.selected_objectives:
        return []

    return [
        objective.strip()
        for objective in session.selected_objectives.split(',')
        if objective.strip()
    ]


def _lesson_to_summary(lesson, summary_text: str, metadata, citations) -> LessonSummary:
    return LessonSummary(
        id=lesson.id,
        title=lesson.title,
        summary=summary_text,
        content=lesson.content,
        metadata=metadata or {},
        citations=citations or [],
    )


@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    repo = SessionRepository()
    standard_repo = StandardsRepository()

    # Handle both new array format and backward compatibility
    standard_ids = request.standard_ids or []
    if request.standard_id and not standard_ids:
        # Backward compatibility: single standard_id
        standard_ids = [request.standard_id]

    # Convert objectives array to comma-separated string for database
    objectives_str = None
    if request.selected_objectives:
        objectives_str = ",".join(request.selected_objectives)

    # Convert standards array to comma-separated string for database
    standards_str = None
    if standard_ids:
        standards_str = ",".join(standard_ids)

    # Convert grade level from display format to storage format
    storage_grade_level = format_grade_for_storage(request.grade_level)

    session = repo.create_session(
        user_id=current_user.id,
        grade_level=storage_grade_level,
        strand_code=request.strand_code,
        standard_id=standards_str,  # Use unified standards string
        additional_context=request.additional_context,
        lesson_duration=request.lesson_duration,
        class_size=request.class_size,
        selected_objectives=objectives_str,
        selected_model=request.selected_model,
    )
    return _session_to_response(session, standard_repo, repo)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
) -> List[SessionResponse]:
    repo = SessionRepository()
    standard_repo = StandardsRepository()
    sessions = repo.list_sessions(current_user.id)
    return [_session_to_response(session, standard_repo, repo) for session in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    repo = SessionRepository()
    session = repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    standard_repo = StandardsRepository()
    return _session_to_response(session, standard_repo, repo)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    repo = SessionRepository()
    session = repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Handle both new array format and backward compatibility
    standard_ids = request.standard_ids or []
    if request.standard_id and not standard_ids:
        # Backward compatibility: single standard_id
        standard_ids = [request.standard_id]

    # Convert objectives array to comma-separated string for database
    objectives_str = None
    if request.selected_objectives:
        objectives_str = ",".join(request.selected_objectives)

    # Convert standards array to comma-separated string for database
    standards_str = None
    if standard_ids:
        standards_str = ",".join(standard_ids)

    # Convert grade level from display format to storage format
    storage_grade_level = format_grade_for_storage(request.grade_level)

    updated = repo.update_session(
        session_id,
        grade_level=storage_grade_level,
        strand_code=request.strand_code,
        standard_id=standards_str,  # Use unified standards string
        additional_context=request.additional_context,
        lesson_duration=request.lesson_duration,
        class_size=request.class_size,
        selected_objective=objectives_str,  # Use unified objectives string
    )
    standard_repo = StandardsRepository()
    return _session_to_response(updated, standard_repo, repo)


@router.delete("")
async def delete_all_sessions(
    current_user: User = Depends(get_current_user),
):
    """Delete all sessions for the current user"""
    repo = SessionRepository()
    lesson_repo = LessonRepository()

    # Get all sessions for the user
    sessions = repo.list_sessions(current_user.id, limit=1000)  # Get all sessions

    # Delete associated lessons for each session
    for session in sessions:
        lessons = lesson_repo.list_lessons_for_session(session.id)
        for lesson in lessons:
            lesson_repo.delete_lesson(lesson.id)

    # Delete all sessions
    deleted_count = repo.delete_all_sessions(current_user.id)

    return {
        "message": f"Deleted {deleted_count} session(s) successfully",
        "count": deleted_count,
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a session and optionally its associated lessons"""
    repo = SessionRepository()
    session = repo.get_session(session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Optionally delete associated lessons
    lesson_repo = LessonRepository()
    lessons = lesson_repo.list_lessons_for_session(session_id)
    for lesson in lessons:
        lesson_repo.delete_lesson(lesson.id)

    # Delete the session
    deleted = repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete session"
        )

    return {"message": "Session deleted successfully"}


def _create_lesson_agent(session: Any, use_conversational: bool = True) -> LessonAgent:
    """Create and initialize a LessonAgent for the session"""
    flow = Flow(name="lesson_planning")
    store = Store()
    standard_repo = StandardsRepository()

    # Import web search service and config
    from backend.services.web_search_service import WebSearchService
    from backend.config import get_config

    # Get web search configuration
    config = get_config()
    web_search_config = config.web_search

    # Initialize web search service if API key is available
    web_search_service = None
    web_search_enabled = bool(web_search_config.api_key)

    if web_search_enabled:
        try:
            web_search_service = WebSearchService(
                api_key=web_search_config.api_key,
                cache_ttl=web_search_config.cache_ttl,
                max_cache_size=web_search_config.max_cache_size,
                timeout=web_search_config.timeout,
                educational_only=web_search_config.educational_only,
                min_relevance_score=web_search_config.min_relevance_score,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize WebSearchService: {e}")
            web_search_enabled = False

    # Use conversational mode by default for more natural interaction
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standard_repo,
        conversational_mode=use_conversational,
        web_search_enabled=web_search_enabled,
        web_search_service=web_search_service,
        selected_model=getattr(session, "selected_model", None),
    )

    # Try to restore agent state from session if available
    if session.agent_state:
        try:
            agent.restore_state(session.agent_state)
            # If we're in conversational mode but restored a form-based state, convert it
            if use_conversational:
                form_based_states = [
                    "welcome",
                    "grade_selection",
                    "strand_selection",
                    "standard_selection",
                    "objective_refinement",
                    "context_collection",
                ]
                if agent.get_state() in form_based_states:
                    # Convert to conversational mode - start fresh in conversational_welcome
                    agent.set_state("conversational_welcome")
        except Exception as e:
            # If restoration fails, continue with fresh agent
            import logging

            logging.warning(f"Failed to restore agent state: {e}")

    # Restore conversation history if available
    if session.conversation_history:
        try:
            import json as json_module

            conversation_history = json_module.loads(session.conversation_history)
            agent.conversation_history = conversation_history
            logger.info(
                f"Restored {len(conversation_history)} messages to conversation history"
            )
        except Exception as e:
            logger.warning(f"Failed to restore conversation history: {e}")

    # Always pre-populate agent with session context if available
    # This ensures that even if state was restored, we have the latest session context
    if session.grade_level:
        agent.lesson_requirements["grade_level"] = session.grade_level
    if session.strand_code:
        agent.lesson_requirements["strand_code"] = session.strand_code
    if session.selected_standards:
        standard = standard_repo.get_standard_by_id(session.selected_standards)
        if standard:
            agent.lesson_requirements["standard"] = standard
            objectives = standard_repo.get_objectives_for_standard(
                session.selected_standards
            )
            agent.lesson_requirements["objectives"] = objectives

    # Add specific selected objectives if available
    if session.selected_objectives:
        agent.lesson_requirements["selected_objectives"] = session.selected_objectives

    # Add additional standards if available
    if session.additional_standards:
        agent.lesson_requirements["additional_standards"] = session.additional_standards

    # Add additional objectives if available
    if session.additional_objectives:
        agent.lesson_requirements["additional_objectives"] = (
            session.additional_objectives
        )

    return agent


def _save_agent_state(
    session_id: str, agent: LessonAgent, session_repo: SessionRepository
) -> None:
    """Save agent state to session for persistence"""
    import json as json_module

    agent_state_json = agent.serialize_state()
    conversation_history = json_module.dumps(agent.get_conversation_history())
    current_state = agent.get_state()

    session_repo.save_agent_state(
        session_id=session_id,
        agent_state=agent_state_json,
        conversation_history=conversation_history,
        current_state=current_state,
    )


def _persist_user_message(
    session_id: str,
    agent: LessonAgent,
    session_repo: SessionRepository,
    message_text: str,
) -> None:
    """Persist the user message and current agent state"""
    conversation_history = agent.get_conversation_history()
    conversation_history.append({"role": "user", "content": message_text})

    agent_state_json = agent.serialize_state()
    conversation_history_json = json.dumps(conversation_history)
    current_state = agent.get_state()

    saved_session = session_repo.save_agent_state(
        session_id=session_id,
        agent_state=agent_state_json,
        conversation_history=conversation_history_json,
        current_state=current_state,
    )

    if not saved_session:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message and save conversation",
        )


@router.get("/{session_id}/models", response_model=ModelAvailabilityResponse)
async def get_available_models(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> ModelAvailabilityResponse:
    """Get available models for the session"""
    session_repo = SessionRepository()
    session = session_repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    model_router = ModelRouter()
    available_models = model_router.get_available_cloud_models()

    # Use default model if session has no selected model, or if selected model is the old default
    default_model_id = config.llm.default_model
    old_default_id = "Qwen/Qwen3-VL-235B-A22B-Instruct"
    
    # If session has old default selected, migrate to new default
    if session.selected_model == old_default_id:
        # Update session to use new default
        session_repo.update_session(session_id, selected_model=default_model_id)
        current_model = default_model_id
    else:
        # Use session's selected model or default
        current_model = session.selected_model or default_model_id

    return ModelAvailabilityResponse(
        available_models=available_models,
        current_model=current_model,
        processing_mode="cloud" if model_router.is_cloud_available() else "local",
    )


@router.put("/{session_id}/models", response_model=SessionResponse)
async def update_selected_model(
    session_id: str,
    request: ModelSelectionRequest,
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """Update the selected model for a session"""
    session_repo = SessionRepository()
    session = session_repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Validate model availability
    if request.selected_model:
        model_router = ModelRouter()
        if not model_router.is_model_available(request.selected_model):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Model {request.selected_model} is not available",
            )

    # Update session with selected model
    updated_session = session_repo.update_session(
        session_id=session_id, selected_model=request.selected_model
    )

    if not updated_session:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session model",
        )

    # Convert to response format
    standard_repo = StandardsRepository()
    session_response = _session_to_response(updated_session, standard_repo, session_repo)

    return session_response


def _compose_lesson_from_agent(
    agent: LessonAgent, current_user: User
) -> Dict[str, Any]:
    """Convert agent lesson requirements into a lesson plan"""
    requirements = agent.get_lesson_requirements()

    standard = requirements.get("standard")
    standard_label = standard.standard_id if standard else "Selected standard"
    grade_label = requirements.get("grade_level", "the chosen grade level")

    # Get file_id for the standard if available
    standard_file_id = None
    if standard and hasattr(standard, "file_id"):
        standard_file_id = standard.file_id

    # Check if an LLM-generated lesson is available
    generated_lesson = requirements.get("generated_lesson")

    if generated_lesson:
        # Use the LLM-generated lesson content
        content = generated_lesson
        title = standard_label
        summary = f"AI-generated lesson for {grade_label} - {standard_label}"
    else:
        # Build lesson content from template
        activities = [
            "Warm-up: Short rhythm clapping inspired by the strand's motif.",
            "Main activity: Guided practice connecting movement, text, and sound.",
            "Closure: Reflective journaling or share-out with peer feedback.",
        ]

        assessment = "Use quick performance checks, exit tickets, or recordings to capture mastery of the targeted objective."

        content_lines = [
            f"Title: {standard_label} Focus",
            f"Overview: Lesson connects {grade_label} learners to {standard_label}.",
            "Activities:",
        ]
        content_lines.extend([f"- {activity}" for activity in activities])
        content_lines.append(f"Assessment: {assessment}")
        content_lines.append(
            "Extensions: Invite students to share cultural connections or create visuals."
        )

        content = "\n".join(content_lines)
        title = standard_label
        summary = f"Lesson connects {grade_label} learners to {standard_label}."

    return {
        "title": title,
        "summary": summary,
        "content": content,
        "metadata": {
            "grade_level": requirements.get("grade_level"),
            "strand_code": requirements.get("strand_code"),
            "standard_id": standard.standard_id if standard else None,
            "duration": requirements.get("duration"),
            "class_size": requirements.get("class_size"),
            "generated_by": "llm" if generated_lesson else "template",
        },
        "citations": [standard.standard_id] if standard else [],
        "citation_file_ids": [standard_file_id]
        if standard and standard_file_id
        else [],
    }


def _generate_draft_payload(
    agent: LessonAgent,
    session: Any,
    current_user: User,
    response_text: str,
    lesson_repo: LessonRepository,
    session_repo: SessionRepository,
    standard_repo: StandardsRepository,
) -> Tuple[LessonSummary, SessionResponse]:
    """Create or update the draft lesson and session response"""
    plan = _compose_lesson_from_agent(agent, current_user)

    lesson = lesson_repo.create_lesson(
        session_id=session.id,
        user_id=current_user.id,
        title=plan["title"],
        content=plan["content"],
        metadata=json.dumps(plan["metadata"]),
        processing_mode=current_user.processing_mode.value,
        is_draft=True,
    )

    session_repo.touch_session(session.id)
    updated_session = session_repo.get_session(session.id)

    lesson_summary = _lesson_to_summary(
        lesson=lesson,
        summary_text=response_text,
        metadata=plan.get("metadata"),
        citations=plan.get("citations", []),
    )

    return lesson_summary, _session_to_response(updated_session, standard_repo, session_repo)


@router.post("/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    session_repo = SessionRepository()
    session = session_repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    standard_repo = StandardsRepository()
    agent = _create_lesson_agent(session)
    lesson_repo = LessonRepository()

    try:
        _persist_user_message(session_id, agent, session_repo, request.message)
        logger.info(f"Conversation history saved for session {session_id}")

        response_text = agent.chat(request.message)
        _save_agent_state(session_id, agent, session_repo)

        lesson_summary, session_payload = _generate_draft_payload(
            agent=agent,
            session=session,
            current_user=current_user,
            response_text=response_text,
            lesson_repo=lesson_repo,
            session_repo=session_repo,
            standard_repo=standard_repo,
        )

        return ChatResponse(
            response=response_text,
            lesson=lesson_summary,
            session=session_payload,
        )

    except Exception as e:
        import traceback

        logger.error(f"Error in send_message for session {session_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Try to save at least the user message if everything else fails
        try:
            conversation_history = [{"role": "user", "content": request.message}]
            session_repo.save_agent_state(
                session_id=session_id,
                agent_state="{}",
                conversation_history=json.dumps(conversation_history),
                current_state="error",
            )
        except Exception as save_error:
            logger.error(f"Failed to save fallback conversation history: {save_error}")

        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message and save conversation",
        )


# Old SSE event function removed - now using emit_stream_event from streaming_schema


@router.post("/{session_id}/messages/stream")
async def stream_message(
    session_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
):
    session_repo = SessionRepository()
    session = session_repo.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")

    standard_repo = StandardsRepository()
    agent = _create_lesson_agent(session)
    lesson_repo = LessonRepository()

    try:
        _persist_user_message(session_id, agent, session_repo, request.message)
        logger.info(f"Conversation history saved for session {session_id}")

        # Now process message through the agent
        response_text = agent.chat(request.message)

        # Add AI response to conversation history
        conversation_history = agent.get_conversation_history()
        conversation_history.append({"role": "assistant", "content": response_text})

        # Save final state with AI response
        final_agent_state_json = agent.serialize_state()
        final_conversation_history_json = json.dumps(conversation_history)
        final_current_state = agent.get_state()

        final_session = session_repo.save_agent_state(
            session_id=session_id,
            agent_state=final_agent_state_json,
            conversation_history=final_conversation_history_json,
            current_state=final_current_state,
        )

        if not final_session:
            logger.error(
                f"Failed to save final conversation state for session {session_id}"
            )
            # Don't fail the request, but log the error

        lesson_summary, session_payload = _generate_draft_payload(
            agent=agent,
            session=session,
            current_user=current_user,
            response_text=response_text,
            lesson_repo=lesson_repo,
            session_repo=session_repo,
            standard_repo=standard_repo,
        )

        async def event_stream():
            # Send confirmation that conversation was persisted
            yield emit_stream_event(
                create_persisted_event(
                    session_updated=final_session is not None,
                    message="Conversation saved successfully"
                )
            )

            yield emit_stream_event(
                create_status_event("PocketMusec is generating a response...")
            )

            # Stream the agent's response in chunks
            sentences = [
                segment.strip()
                for segment in response_text.split(". ")
                if segment.strip()
            ]
            for sentence in sentences:
                text = sentence if sentence.endswith(".") else sentence + "."
                yield emit_stream_event(create_delta_event(text))
                await asyncio.sleep(0.1)

            payload_dict = {
                "response": response_text,
                "lesson": json.loads(lesson_summary.model_dump_json()),
                "session": json.loads(session_payload.model_dump_json())
            }

            yield emit_stream_event(
                create_complete_event(payload_dict)
            )

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in stream_message for session {session_id}: {e}")
        # Try to save at least the user message if everything else fails
        try:
            conversation_history = [{"role": "user", "content": request.message}]
            session_repo.save_agent_state(
                session_id=session_id,
                agent_state="{}",
                conversation_history=json.dumps(conversation_history),
                current_state="error",
            )
        except Exception as save_error:
            logger.error(f"Failed to save fallback conversation history: {save_error}")

        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message and save conversation",
        )
