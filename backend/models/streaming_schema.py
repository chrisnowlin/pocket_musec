"""Shared streaming event schema for harmonizing SSE and job status responses"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional, Union
from datetime import datetime
import json


class StreamingEventType(str, Enum):
    """Standardized streaming event types"""
    DELTA = "delta"
    STATUS = "status"
    PERSISTED = "persisted"
    COMPLETE = "complete"
    ERROR = "error"
    PROGRESS = "progress"


@dataclass
class StreamingEvent:
    """Standardized streaming event structure"""
    type: StreamingEventType
    payload: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_sse_format(self) -> str:
        """Convert to Server-Sent Events format"""
        return f"data: {json.dumps(asdict(self))}\n\n"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class JobStatusEnvelope:
    """Standardized job status envelope for presentation jobs and other background tasks"""
    status: str  # pending, running, completed, failed, cancelled
    progress: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# Helper functions for creating common event types


def create_delta_event(text: str, meta: Optional[Dict[str, Any]] = None) -> StreamingEvent:
    """Create a delta event for streaming text/content"""
    return StreamingEvent(
        type=StreamingEventType.DELTA,
        payload={"text": text},
        meta=meta
    )


def create_status_event(message: str, meta: Optional[Dict[str, Any]] = None) -> StreamingEvent:
    """Create a status event for progress updates"""
    return StreamingEvent(
        type=StreamingEventType.STATUS,
        payload={"message": message},
        meta=meta
    )


def create_persisted_event(
    session_updated: bool = True,
    message: str = "Conversation saved successfully",
    meta: Optional[Dict[str, Any]] = None
) -> StreamingEvent:
    """Create a persisted event for save confirmations"""
    return StreamingEvent(
        type=StreamingEventType.PERSISTED,
        payload={
            "message": message,
            "session_updated": session_updated
        },
        meta=meta
    )


def create_complete_event(
    payload: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None
) -> StreamingEvent:
    """Create a complete event with final response data"""
    return StreamingEvent(
        type=StreamingEventType.COMPLETE,
        payload=payload,
        meta=meta
    )


def create_error_event(
    error_message: str,
    error_code: Optional[str] = None,
    retry_recommended: bool = False,
    meta: Optional[Dict[str, Any]] = None
) -> StreamingEvent:
    """Create an error event"""
    error_payload = {
        "message": error_message,
        "retry_recommended": retry_recommended
    }
    if error_code:
        error_payload["code"] = error_code

    return StreamingEvent(
        type=StreamingEventType.ERROR,
        payload=error_payload,
        meta=meta
    )


def create_progress_event(
    progress: Union[int, float],
    total: Optional[Union[int, float]] = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> StreamingEvent:
    """Create a progress event for tracking completion"""
    progress_payload = {"progress": progress}
    if total is not None:
        progress_payload["total"] = total
    if message:
        progress_payload["message"] = message

    return StreamingEvent(
        type=StreamingEventType.PROGRESS,
        payload=progress_payload,
        meta=meta
    )


def create_job_status_envelope(
    status: str,
    progress: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None,
    error: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> JobStatusEnvelope:
    """Create a standardized job status envelope"""
    return JobStatusEnvelope(
        status=status,
        progress=progress,
        retry_after=retry_after,
        error=error,
        meta=meta
    )


# SSE emission helper


def emit_stream_event(event: StreamingEvent) -> str:
    """Emit a streaming event in SSE format"""
    return event.to_sse_format()


# Parser for frontend consumption
def parse_sse_chunk(chunk: str) -> Optional[StreamingEvent]:
    """Parse SSE chunk string into StreamingEvent"""
    if not chunk.startswith('data:'):
        return None

    payload = chunk.replace('data:', '', 1).strip()
    if not payload or payload == '[DONE]':
        return None

    try:
        data = json.loads(payload)
        return StreamingEvent(**data)
    except json.JSONDecodeError:
        return None
    except Exception:
        # If parsing fails, return a basic error event
        return create_error_event("Failed to parse event chunk")