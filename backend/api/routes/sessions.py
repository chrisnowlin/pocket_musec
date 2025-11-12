"""Lesson session and chat endpoints"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ...repositories.session_repository import SessionRepository
from ...repositories.lesson_repository import LessonRepository
from ...repositories.standards_repository import StandardsRepository
from ...pocketflow.lesson_agent import LessonAgent
from ...pocketflow.flow import Flow
from ...pocketflow.store import Store
from ..models import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    ChatMessageRequest,
    ChatResponse,
    LessonSummary,
    StandardResponse,
)
from ..dependencies import get_current_user
from ...auth import User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _standard_to_response(standard, repo: StandardsRepository) -> StandardResponse:
    objectives = repo.get_objectives_for_standard(standard.standard_id)
    learning_objectives = [obj.objective_text for obj in objectives][:3]
    return StandardResponse(
        id=standard.standard_id,
        code=standard.standard_id,
        grade=standard.grade_level,
        strand_code=standard.strand_code,
        strand_name=standard.strand_name,
        title=standard.standard_text,
        description=standard.strand_description,
        objectives=len(objectives),
        learning_objectives=learning_objectives,
    )


def _session_to_response(session, repo: StandardsRepository) -> SessionResponse:
    standard_resp = None
    if session.selected_standards:
        standard = repo.get_standard_by_id(session.selected_standards)
        if standard:
            standard_resp = _standard_to_response(standard, repo)

    return SessionResponse(
        id=session.id,
        grade_level=session.grade_level,
        strand_code=session.strand_code,
        selected_standard=standard_resp,
        additional_context=session.additional_context,
        conversation_history=session.conversation_history,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


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
    session = repo.create_session(
        user_id=current_user.id,
        grade_level=request.grade_level,
        strand_code=request.strand_code,
        standard_id=request.standard_id,
        additional_context=request.additional_context,
    )
    return _session_to_response(session, standard_repo)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
) -> List[SessionResponse]:
    repo = SessionRepository()
    standard_repo = StandardsRepository()
    sessions = repo.list_sessions(current_user.id)
    return [_session_to_response(session, standard_repo) for session in sessions]


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
    return _session_to_response(session, standard_repo)


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

    updated = repo.update_session(
        session_id,
        grade_level=request.grade_level,
        strand_code=request.strand_code,
        standard_id=request.standard_id,
        additional_context=request.additional_context,
    )
    standard_repo = StandardsRepository()
    return _session_to_response(updated, standard_repo)


def _create_lesson_agent(session: Any, use_conversational: bool = True) -> LessonAgent:
    """Create and initialize a LessonAgent for the session"""
    flow = Flow(name="lesson_planning")
    store = Store()
    standard_repo = StandardsRepository()

    # Use conversational mode by default for more natural interaction
    agent = LessonAgent(
        flow=flow,
        store=store,
        standards_repo=standard_repo,
        conversational_mode=use_conversational,
    )

    # Try to restore agent state from session if available
    if session.agent_state:
        try:
            agent.restore_state(session.agent_state)
            return agent
        except Exception as e:
            # If restoration fails, continue with fresh agent
            import logging

            logging.warning(f"Failed to restore agent state: {e}")

    # Pre-populate agent with session context if available
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


def _compose_lesson_from_agent(
    agent: LessonAgent, current_user: User
) -> Dict[str, Any]:
    """Convert agent lesson requirements into a lesson plan"""
    requirements = agent.get_lesson_requirements()

    standard = requirements.get("standard")
    standard_label = standard.standard_id if standard else "Selected standard"
    grade_label = requirements.get("grade_level", "the chosen grade level")

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
    }


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

    # Process message through the agent
    response_text = agent.chat(request.message)

    # Save agent state for persistence
    _save_agent_state(session_id, agent, session_repo)

    # Compose lesson from agent's current state
    plan = _compose_lesson_from_agent(agent, current_user)

    lesson = lesson_repo.create_lesson(
        session_id=session.id,
        user_id=current_user.id,
        title=plan["title"],
        content=plan["content"],
        metadata=json.dumps(plan["metadata"]),
        processing_mode=current_user.processing_mode.value,
        is_draft=True,  # Save all generated lessons as drafts by default
    )

    session_repo.touch_session(session_id)
    updated_session = session_repo.get_session(session_id)

    lesson_summary = _lesson_to_summary(
        lesson=lesson,
        summary_text=response_text,
        metadata=plan.get("metadata"),
        citations=plan.get("citations", []),
    )

    return ChatResponse(
        response=response_text,
        lesson=lesson_summary,
        session=_session_to_response(updated_session, standard_repo),
    )


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


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

    # Process message through the agent
    response_text = agent.chat(request.message)

    # Save agent state for persistence
    _save_agent_state(session_id, agent, session_repo)

    # Compose lesson from agent's current state
    plan = _compose_lesson_from_agent(agent, current_user)

    lesson = lesson_repo.create_lesson(
        session_id=session.id,
        user_id=current_user.id,
        title=plan["title"],
        content=plan["content"],
        metadata=json.dumps(plan["metadata"]),
        processing_mode=current_user.processing_mode.value,
        is_draft=True,  # Save all generated lessons as drafts by default
    )

    session_repo.touch_session(session_id)
    updated_session = session_repo.get_session(session_id)
    lesson_summary = _lesson_to_summary(
        lesson=lesson,
        summary_text=response_text,
        metadata=plan.get("metadata"),
        citations=plan.get("citations", []),
    )

    async def event_stream():
        yield _sse_event(
            {"type": "status", "message": "PocketMusec is generating a response..."}
        )
        # Stream the agent's response in chunks
        sentences = [
            segment.strip() for segment in response_text.split(". ") if segment.strip()
        ]
        for sentence in sentences:
            text = sentence if sentence.endswith(".") else sentence + "."
            yield _sse_event({"type": "delta", "text": text})
            await asyncio.sleep(0.1)

        payload = ChatResponse(
            response=response_text,
            lesson=lesson_summary,
            session=_session_to_response(updated_session, standard_repo),
        )
        yield _sse_event(
            {"type": "complete", "payload": json.loads(payload.model_dump_json())}
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
