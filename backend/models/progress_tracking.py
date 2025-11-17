"""Enhanced progress tracking models for presentation generation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import time
import json


class ProgressStep(str, Enum):
    """Individual steps in the presentation generation process."""

    INITIALIZING = "initializing"
    FETCHING_LESSON = "fetching_lesson"
    VALIDATING_ACCESS = "validating_access"
    MARKING_STALE = "marking_stale"
    BUILDING_SCAFFOLD = "building_scaffold"
    CREATING_PRESENTATION = "creating_presentation"
    LLM_POLISH_REQUEST = "llm_polish_request"
    LLM_POLISH_PROCESSING = "llm_polish_processing"
    UPDATING_SLIDES = "updating_slides"
    GENERATING_EXPORTS = "generating_exports"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


@dataclass
class StepProgress:
    """Progress information for a specific step."""

    step: ProgressStep
    name: str
    description: str
    weight: float = 1.0  # Weight in overall progress (0.0 to 1.0)
    status: str = "pending"  # pending, running, completed, failed, skipped
    progress_percent: float = 0.0  # 0.0 to 100.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[float] = None
    actual_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark step as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.progress_percent = 0.0

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update step progress."""
        self.progress_percent = max(0.0, min(100.0, progress))
        if message:
            self.details["current_message"] = message

    def complete(self, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0

        if self.started_at:
            self.actual_duration_seconds = (self.completed_at - self.started_at).total_seconds()

        if details:
            self.details.update(details)

    def fail(self, error_message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

        if self.started_at:
            self.actual_duration_seconds = (self.completed_at - self.started_at).total_seconds()

        if details:
            self.details.update(details)

    def skip(self, reason: str = "Skipped") -> None:
        """Mark step as skipped."""
        self.status = "skipped"
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        self.details["skip_reason"] = reason


@dataclass
class DetailedProgress:
    """Comprehensive progress tracking for presentation generation."""

    job_id: str
    current_step: Optional[ProgressStep] = None
    steps: List[StepProgress] = field(default_factory=list)
    overall_progress: float = 0.0  # 0.0 to 100.0
    estimated_time_remaining_seconds: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    current_message: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize default steps if none provided."""
        if not self.steps:
            self.steps = self._create_default_steps()

    def _create_default_steps(self) -> List[StepProgress]:
        """Create default progress steps with weights."""
        return [
            StepProgress(
                step=ProgressStep.INITIALIZING,
                name="Initializing",
                description="Setting up presentation generation",
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
            StepProgress(
                step=ProgressStep.FETCHING_LESSON,
                name="Fetching Lesson",
                description="Retrieving lesson document from database",
                weight=0.10,
                estimated_duration_seconds=2.0
            ),
            StepProgress(
                step=ProgressStep.VALIDATING_ACCESS,
                name="Validating Access",
                description="Checking user permissions and lesson ownership",
                weight=0.05,
                estimated_duration_seconds=0.5
            ),
            StepProgress(
                step=ProgressStep.MARKING_STALE,
                name="Marking Old Presentations",
                description="Marking existing presentations as stale",
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
            StepProgress(
                step=ProgressStep.BUILDING_SCAFFOLD,
                name="Building Scaffold",
                description="Creating basic presentation structure",
                weight=0.20,
                estimated_duration_seconds=5.0
            ),
            StepProgress(
                step=ProgressStep.CREATING_PRESENTATION,
                name="Creating Presentation",
                description="Setting up presentation record in database",
                weight=0.10,
                estimated_duration_seconds=2.0
            ),
            StepProgress(
                step=ProgressStep.LLM_POLISH_REQUEST,
                name="Preparing LLM Polish",
                description="Preparing content for LLM enhancement",
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
            StepProgress(
                step=ProgressStep.LLM_POLISH_PROCESSING,
                name="LLM Polishing",
                description="Enhancing content with AI polish",
                weight=0.15,
                estimated_duration_seconds=20.0
            ),
            StepProgress(
                step=ProgressStep.UPDATING_SLIDES,
                name="Updating Slides",
                description="Saving final slides to database",
                weight=0.10,
                estimated_duration_seconds=2.0
            ),
            StepProgress(
                step=ProgressStep.GENERATING_EXPORTS,
                name="Generating Exports",
                description="Creating export files (JSON, Markdown, PPTX, PDF)",
                weight=0.15,
                estimated_duration_seconds=8.0
            ),
            StepProgress(
                step=ProgressStep.FINALIZING,
                name="Finalizing",
                description="Final setup and cleanup",
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
        ]

    def start_step(self, step: ProgressStep, message: str = "") -> None:
        """Start a new step."""
        self.current_step = step
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.start()
            if message:
                step_obj.details["current_message"] = message
                self.current_message = message

        self._update_overall_progress()

    def update_step_progress(
        self,
        step: ProgressStep,
        progress: float = None,
        message: str = "",
        details: Dict[str, Any] = None
    ) -> None:
        """Update progress for the current step."""
        step_obj = self._get_step(step)
        if not step_obj:
            return

        if progress is not None:
            step_obj.update_progress(progress, message)
        elif message:
            step_obj.details["current_message"] = message

        if details:
            step_obj.details.update(details)

        self.current_message = message or step_obj.description

        # Update time remaining estimate
        self._estimate_time_remaining()

        # Update overall progress
        self._update_overall_progress()

        self.last_updated = datetime.utcnow()

    def complete_step(
        self,
        step: ProgressStep,
        result_details: Optional[Dict[str, Any]] = None,
        skip_step: bool = False
    ) -> None:
        """Complete the current step."""
        step_obj = self._get_step(step)
        if step_obj:
            if skip_step:
                step_obj.skip(result_details.get("reason") if result_details else "Skipped")
            else:
                step_obj.complete(result_details)

        self._update_overall_progress()
        self._estimate_time_remaining()
        self.last_updated = datetime.utcnow()

    def fail_step(
        self,
        step: ProgressStep,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark a step as failed."""
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.fail(error_message, error_details)

        self.current_message = f"Step failed: {step_obj.name if step_obj else step} - {error_message}"
        self.last_updated = datetime.utcnow()

    def _get_step(self, step: ProgressStep) -> Optional[StepProgress]:
        """Get step object by enum value."""
        for step_obj in self.steps:
            if step_obj.step == step:
                return step_obj
        return None

    def _update_overall_progress(self) -> None:
        """Calculate overall progress based on completed steps."""
        total_weight = sum(step.weight for step in self.steps)
        completed_weight = 0.0
        in_progress_weight = 0.0

        for step in self.steps:
            if step.status == "completed" or step.status == "skipped":
                completed_weight += step.weight
            elif step.status == "running":
                completed_weight += step.weight * (step.progress_percent / 100.0)

        self.overall_progress = (completed_weight / total_weight) * 100.0 if total_weight > 0 else 0.0

    def _estimate_time_remaining(self) -> None:
        """Estimate time remaining based on current progress and step timing."""
        completed_steps = [s for s in self.steps if s.status in ["completed", "skipped"]]
        running_step = next((s for s in self.steps if s.status == "running"), None)
        pending_steps = [s for s in self.steps if s.status == "pending"]

        # If no steps are running or completed, use estimates
        if not completed_steps and not running_step:
            total_estimated = sum(s.estimated_duration_seconds or 1.0 for s in pending_steps)
            self.estimated_time_remaining_seconds = total_estimated
            if self.estimated_time_remaining_seconds:
                self.estimated_completion_time = datetime.utcnow() + timedelta(seconds=self.estimated_time_remaining_seconds)
            return

        # Use actual duration data where available, fallback to estimates
        total_remaining_time = 0.0

        # Add remaining time for currently running step
        if running_step:
            if running_step.estimated_duration_seconds and running_step.started_at:
                elapsed = (datetime.utcnow() - running_step.started_at).total_seconds()
                remaining = max(0, running_step.estimated_duration_seconds - elapsed)
                total_remaining_time += remaining * (1.0 - running_step.progress_percent / 100.0)
            else:
                # Use simple linear extrapolation if no estimate available
                if running_step.progress_percent > 0 and running_step.started_at:
                    elapsed = (datetime.utcnow() - running_step.started_at).total_seconds()
                    estimated_total = elapsed * (100.0 / running_step.progress_percent)
                    remaining = max(0, estimated_total - elapsed)
                else:
                    remaining = 60.0  # Default to 1 minute

                total_remaining_time += remaining * (1.0 - running_step.progress_percent / 100.0)

        # Add estimated time for pending steps
        for step in pending_steps:
            total_remaining_time += step.estimated_duration_seconds or 10.0

        self.estimated_time_remaining_seconds = total_remaining_time
        if self.estimated_time_remaining_seconds:
            self.estimated_completion_time = datetime.utcnow() + timedelta(seconds=self.estimated_time_remaining_seconds)

    def get_current_step_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current step."""
        if not self.current_step:
            return None

        step_obj = self._get_step(self.current_step)
        if not step_obj:
            return None

        return {
            "step": step_obj.step.value,
            "name": step_obj.name,
            "description": step_obj.description,
            "progress": step_obj.progress_percent,
            "status": step_obj.status,
            "started_at": step_obj.started_at.isoformat() if step_obj.started_at else None,
            "message": step_obj.details.get("current_message", ""),
        }

    def get_step_list(self) -> List[Dict[str, Any]]:
        """Get a list of all steps with their progress."""
        return [
            {
                "step": step_obj.step.value,
                "name": step_obj.name,
                "description": step_obj.description,
                "status": step_obj.status,
                "progress": step_obj.progress_percent,
                "weight": step_obj.weight,
                "started_at": step_obj.started_at.isoformat() if step_obj.started_at else None,
                "completed_at": step_obj.completed_at.isoformat() if step_obj.completed_at else None,
                "estimated_duration": step_obj.estimated_duration_seconds,
                "actual_duration": step_obj.actual_duration_seconds,
                "error_message": step_obj.error_message,
                "details": step_obj.details,
            }
            for step_obj in self.steps
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "current_step": self.current_step.value if self.current_step else None,
            "current_step_info": self.get_current_step_info(),
            "overall_progress": round(self.overall_progress, 1),
            "estimated_time_remaining_seconds": self.estimated_time_remaining_seconds,
            "estimated_completion_time": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            "current_message": self.current_message,
            "last_updated": self.last_updated.isoformat(),
            "steps": self.get_step_list(),
        }


@dataclass
class ProgressUpdate:
    """A progress update message for real-time communication."""

    job_id: str
    progress: DetailedProgress
    timestamp: datetime = field(default_factory=datetime.utcnow)
    update_type: str = "progress"  # progress, step_complete, step_failed, job_complete, job_failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "update_type": self.update_type,
            "timestamp": self.timestamp.isoformat(),
            "progress": self.progress.to_dict(),
        }