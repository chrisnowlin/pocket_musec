"""Advanced export progress tracking models for comprehensive feedback."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import time
import json
import uuid


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    PPTX = "pptx"
    PDF = "pdf"


class ExportStep(str, Enum):
    """Individual steps in the export process for each format."""

    # Common steps for all formats
    INITIALIZING = "initializing"
    VALIDATING_PRESENTATION = "validating_presentation"
    PREPARING_CONTENT = "preparing_content"

    # Format-specific steps
    JSON_SERIALIZING = "json_serializing"
    JSON_VALIDATING = "json_validating"

    MARKDOWN_FORMATTING = "markdown_formatting"
    MARKDOWN_STYLING = "markdown_styling"

    PPTX_CREATING_PRESENTATION = "pptx_creating_presentation"
    PPTX_ADDING_SLIDES = "pptx_adding_slides"
    PPTX_APPLYING_STYLES = "pptx_applying_styles"
    PPTX_SAVING = "pptx_saving"

    PDF_CREATING_DOCUMENT = "pdf_creating_document"
    PDF_ADDING_CONTENT = "pdf_adding_content"
    PDF_FORMATTING = "pdf_formatting"
    PDF_RENDERING = "pdf_rendering"
    PDF_SAVING = "pdf_saving"

    # Common steps
    VALIDATING_OUTPUT = "validating_output"
    CALCULATING_SIZE = "calculating_size"
    GENERATING_FILENAME = "generating_filename"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportStatus(str, Enum):
    """Overall export job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ExportStepProgress:
    """Progress information for a specific export step."""

    step: ExportStep
    name: str
    description: str
    format: ExportFormat
    weight: float = 1.0  # Weight in overall export progress (0.0 to 1.0)
    status: str = "pending"  # pending, running, completed, failed, skipped, cancelled
    progress_percent: float = 0.0  # 0.0 to 100.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[float] = None
    actual_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
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

    def fail(self, error_message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_code = error_code

        if self.started_at:
            self.actual_duration_seconds = (self.completed_at - self.started_at).total_seconds()

        if details:
            self.details.update(details)

    def cancel(self, reason: str = "Cancelled") -> None:
        """Mark step as cancelled."""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
        self.details["cancel_reason"] = reason

    def skip(self, reason: str = "Skipped") -> None:
        """Mark step as skipped."""
        self.status = "skipped"
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        self.details["skip_reason"] = reason


@dataclass
class ExportFormatProgress:
    """Progress tracking for a specific export format."""

    export_id: str
    format: ExportFormat
    status: ExportStatus = ExportStatus.PENDING
    overall_progress: float = 0.0  # 0.0 to 100.0
    file_size_bytes: Optional[int] = None
    filename: Optional[str] = None
    estimated_file_size_bytes: Optional[int] = None
    quality_score: Optional[float] = None  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    steps: List[ExportStepProgress] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Initialize default steps if none provided."""
        if not self.steps:
            self.steps = self._create_default_steps()

    def _create_default_steps(self) -> List[ExportStepProgress]:
        """Create default steps for this export format."""
        base_steps = [
            ExportStepProgress(
                step=ExportStep.INITIALIZING,
                name="Initializing Export",
                description=f"Setting up {self.format.value.upper()} export",
                format=self.format,
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
            ExportStepProgress(
                step=ExportStep.VALIDATING_PRESENTATION,
                name="Validating Presentation",
                description="Checking presentation data and permissions",
                format=self.format,
                weight=0.05,
                estimated_duration_seconds=2.0
            ),
            ExportStepProgress(
                step=ExportStep.PREPARING_CONTENT,
                name="Preparing Content",
                description="Extracting and organizing presentation content",
                format=self.format,
                weight=0.10,
                estimated_duration_seconds=3.0
            )
        ]

        format_specific_steps = []

        if self.format == ExportFormat.JSON:
            format_specific_steps = [
                ExportStepProgress(
                    step=ExportStep.JSON_SERIALIZING,
                    name="Serializing JSON",
                    description="Converting presentation to JSON format",
                    format=self.format,
                    weight=0.30,
                    estimated_duration_seconds=4.0
                ),
                ExportStepProgress(
                    step=ExportStep.JSON_VALIDATING,
                    name="Validating JSON",
                    description="Ensuring JSON structure is valid",
                    format=self.format,
                    weight=0.15,
                    estimated_duration_seconds=2.0
                )
            ]
        elif self.format == ExportFormat.MARKDOWN:
            format_specific_steps = [
                ExportStepProgress(
                    step=ExportStep.MARKDOWN_FORMATTING,
                    name="Formatting Markdown",
                    description="Converting content to Markdown format",
                    format=self.format,
                    weight=0.35,
                    estimated_duration_seconds=5.0
                ),
                ExportStepProgress(
                    step=ExportStep.MARKDOWN_STYLING,
                    name="Styling Markdown",
                    description="Applying Markdown formatting and structure",
                    format=self.format,
                    weight=0.15,
                    estimated_duration_seconds=3.0
                )
            ]
        elif self.format == ExportFormat.PPTX:
            format_specific_steps = [
                ExportStepProgress(
                    step=ExportStep.PPTX_CREATING_PRESENTATION,
                    name="Creating PowerPoint",
                    description="Initializing PowerPoint presentation",
                    format=self.format,
                    weight=0.10,
                    estimated_duration_seconds=3.0
                ),
                ExportStepProgress(
                    step=ExportStep.PPTX_ADDING_SLIDES,
                    name="Adding Slides",
                    description="Adding content slides to presentation",
                    format=self.format,
                    weight=0.35,
                    estimated_duration_seconds=15.0
                ),
                ExportStepProgress(
                    step=ExportStep.PPTX_APPLYING_STYLES,
                    name="Applying Styles",
                    description="Formatting slides and applying styles",
                    format=self.format,
                    weight=0.15,
                    estimated_duration_seconds=5.0
                ),
                ExportStepProgress(
                    step=ExportStep.PPTX_SAVING,
                    name="Saving PPTX",
                    description="Saving final PowerPoint file",
                    format=self.format,
                    weight=0.10,
                    estimated_duration_seconds=4.0
                )
            ]
        elif self.format == ExportFormat.PDF:
            format_specific_steps = [
                ExportStepProgress(
                    step=ExportStep.PDF_CREATING_DOCUMENT,
                    name="Creating PDF Document",
                    description="Initializing PDF document structure",
                    format=self.format,
                    weight=0.10,
                    estimated_duration_seconds=3.0
                ),
                ExportStepProgress(
                    step=ExportStep.PDF_ADDING_CONTENT,
                    name="Adding Content",
                    description="Adding presentation content to PDF",
                    format=self.format,
                    weight=0.30,
                    estimated_duration_seconds=20.0
                ),
                ExportStepProgress(
                    step=ExportStep.PDF_FORMATTING,
                    name="Formatting PDF",
                    description="Applying PDF formatting and layout",
                    format=self.format,
                    weight=0.15,
                    estimated_duration_seconds=8.0
                ),
                ExportStepProgress(
                    step=ExportStep.PDF_RENDERING,
                    name="Rendering PDF",
                    description="Final PDF rendering and optimization",
                    format=self.format,
                    weight=0.20,
                    estimated_duration_seconds=10.0
                ),
                ExportStepProgress(
                    step=ExportStep.PDF_SAVING,
                    name="Saving PDF",
                    description="Saving final PDF file",
                    format=self.format,
                    weight=0.10,
                    estimated_duration_seconds=4.0
                )
            ]

        final_steps = [
            ExportStepProgress(
                step=ExportStep.VALIDATING_OUTPUT,
                name="Validating Output",
                description="Final validation of generated export",
                format=self.format,
                weight=0.10,
                estimated_duration_seconds=2.0
            ),
            ExportStepProgress(
                step=ExportStep.CALCULATING_SIZE,
                name="Calculating Size",
                description="Determining file size and properties",
                format=self.format,
                weight=0.05,
                estimated_duration_seconds=1.0
            ),
            ExportStepProgress(
                step=ExportStep.GENERATING_FILENAME,
                name="Generating Filename",
                description="Creating final filename and metadata",
                format=self.format,
                weight=0.05,
                estimated_duration_seconds=0.5
            ),
            ExportStepProgress(
                step=ExportStep.COMPLETED,
                name="Export Completed",
                description=f"{self.format.value.upper()} export completed successfully",
                format=self.format,
                weight=0.05,
                estimated_duration_seconds=0.5
            )
        ]

        return base_steps + format_specific_steps + final_steps

    def start_export(self) -> None:
        """Start the export process."""
        self.status = ExportStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        # Start first step
        if self.steps:
            self.steps[0].start()

    def start_step(self, step: ExportStep) -> None:
        """Start a specific step."""
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.start()
            self.last_updated = datetime.utcnow()
            self._update_overall_progress()

    def update_step_progress(self, step: ExportStep, progress: float, message: str = "", details: Dict[str, Any] = None) -> None:
        """Update progress for a specific step."""
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.update_progress(progress, message)
            if details:
                step_obj.details.update(details)
            self.last_updated = datetime.utcnow()
            self._update_overall_progress()

    def complete_step(self, step: ExportStep, details: Dict[str, Any] = None) -> None:
        """Complete a specific step."""
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.complete(details)
            self.last_updated = datetime.utcnow()
            self._update_overall_progress()

            # Start next step if there is one
            current_index = next((i for i, s in enumerate(self.steps) if s.step == step), -1)
            if current_index >= 0 and current_index < len(self.steps) - 1:
                next_step = self.steps[current_index + 1]
                next_step.start()

    def fail_step(self, step: ExportStep, error_message: str, error_code: Optional[str] = None, details: Dict[str, Any] = None) -> None:
        """Mark a step as failed."""
        step_obj = self._get_step(step)
        if step_obj:
            step_obj.fail(error_message, error_code, details)
            self.error_message = f"Step failed: {step_obj.name} - {error_message}"
            self.error_code = error_code
            self.status = ExportStatus.FAILED
            self.last_updated = datetime.utcnow()

    def cancel_export(self, reason: str = "User cancelled") -> None:
        """Cancel the export."""
        self.status = ExportStatus.CANCELLED
        self.last_updated = datetime.utcnow()
        # Cancel current step
        for step in self.steps:
            if step.status == "running":
                step.cancel(reason)
                break

    def complete_export(self, file_size_bytes: int, filename: str, quality_score: Optional[float] = None) -> None:
        """Mark the export as completed."""
        self.status = ExportStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.file_size_bytes = file_size_bytes
        self.filename = filename
        self.quality_score = quality_score
        self.overall_progress = 100.0

        # Complete all remaining steps
        for step in self.steps:
            if step.status != "completed":
                step.complete()

        self.last_updated = datetime.utcnow()

    def retry_export(self) -> bool:
        """Attempt to retry the export."""
        if self.retry_count >= self.max_retries:
            return False

        self.retry_count += 1
        self.status = ExportStatus.RETRYING
        self.error_message = None
        self.error_code = None

        # Reset failed steps
        for step in self.steps:
            if step.status == "failed":
                step.status = "pending"
                step.progress_percent = 0.0
                step.error_message = None
                step.started_at = None
                step.completed_at = None
                step.actual_duration_seconds = None

        return True

    def _get_step(self, step: ExportStep) -> Optional[ExportStepProgress]:
        """Get step object by enum value."""
        for step_obj in self.steps:
            if step_obj.step == step:
                return step_obj
        return None

    def _update_overall_progress(self) -> None:
        """Calculate overall progress based on completed steps."""
        total_weight = sum(step.weight for step in self.steps)
        completed_weight = 0.0

        for step in self.steps:
            if step.status in ["completed", "skipped"]:
                completed_weight += step.weight
            elif step.status == "running":
                completed_weight += step.weight * (step.progress_percent / 100.0)

        self.overall_progress = (completed_weight / total_weight) * 100.0 if total_weight > 0 else 0.0

    def get_estimated_time_remaining_seconds(self) -> Optional[float]:
        """Estimate time remaining for this export."""
        completed_steps = [s for s in self.steps if s.status in ["completed", "skipped"]]
        running_step = next((s for s in self.steps if s.status == "running"), None)
        pending_steps = [s for s in self.steps if s.status == "pending"]

        if not completed_steps and not running_step:
            # Use estimates for all pending steps
            return sum(s.estimated_duration_seconds or 1.0 for s in pending_steps)

        total_remaining = 0.0

        # Add remaining time for running step
        if running_step and running_step.estimated_duration_seconds and running_step.started_at:
            elapsed = (datetime.utcnow() - running_step.started_at).total_seconds()
            remaining = max(0, running_step.estimated_duration_seconds - elapsed)
            total_remaining += remaining * (1.0 - running_step.progress_percent / 100.0)

        # Add estimated time for pending steps
        total_remaining += sum(s.estimated_duration_seconds or 5.0 for s in pending_steps)

        return total_remaining

    def get_current_step_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current step."""
        current_step = next((s for s in self.steps if s.status == "running"), None)
        if not current_step:
            return None

        return {
            "step": current_step.step.value,
            "name": current_step.name,
            "description": current_step.description,
            "progress": current_step.progress_percent,
            "status": current_step.status,
            "started_at": current_step.started_at.isoformat() if current_step.started_at else None,
            "message": current_step.details.get("current_message", ""),
            "estimated_duration": current_step.estimated_duration_seconds,
            "actual_duration": current_step.actual_duration_seconds,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "export_id": self.export_id,
            "format": self.format.value,
            "status": self.status.value,
            "overall_progress": round(self.overall_progress, 1),
            "file_size_bytes": self.file_size_bytes,
            "estimated_file_size_bytes": self.estimated_file_size_bytes,
            "filename": self.filename,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_updated": self.last_updated.isoformat(),
            "current_step": self.get_current_step_info(),
            "estimated_time_remaining": self.get_estimated_time_remaining_seconds(),
            "steps": [
                {
                    "step": step.step.value,
                    "name": step.name,
                    "description": step.description,
                    "status": step.status,
                    "progress": step.progress_percent,
                    "weight": step.weight,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "estimated_duration": step.estimated_duration_seconds,
                    "actual_duration": step.actual_duration_seconds,
                    "error_message": step.error_message,
                    "error_code": step.error_code,
                    "details": step.details,
                }
                for step in self.steps
            ]
        }


@dataclass
class BulkExportProgress:
    """Progress tracking for bulk export operations (multiple formats)."""

    bulk_export_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    presentation_id: str = ""
    user_id: str = ""
    formats: List[ExportFormat] = field(default_factory=list)
    status: ExportStatus = ExportStatus.PENDING
    overall_progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    export_progress: Dict[ExportFormat, ExportFormatProgress] = field(default_factory=dict)
    successful_exports: List[ExportFormat] = field(default_factory=list)
    failed_exports: List[ExportFormat] = field(default_factory=list)
    cancelled_exports: List[ExportFormat] = field(default_factory=list)
    error_message: Optional[str] = None
    concurrent_exports: int = 2  # Max simultaneous exports
    download_zip_path: Optional[str] = None

    def start_bulk_export(self) -> None:
        """Start the bulk export process."""
        self.status = ExportStatus.RUNNING
        self.started_at = datetime.utcnow()

        # Initialize format-specific progress trackers
        for format in self.formats:
            if format not in self.export_progress:
                export_progress = ExportFormatProgress(
                    export_id=str(uuid.uuid4()),
                    format=format
                )
                self.export_progress[format] = export_progress

    def update_format_progress(self, format: ExportFormat, format_progress: ExportFormatProgress) -> None:
        """Update progress for a specific format."""
        self.export_progress[format] = format_progress
        self._update_overall_progress()
        self._update_status()

    def complete_format_export(self, format: ExportFormat, file_size_bytes: int, filename: str) -> None:
        """Mark a format export as completed."""
        if format in self.export_progress:
            self.export_progress[format].complete_export(file_size_bytes, filename)

            if format not in self.successful_exports:
                self.successful_exports.append(format)

        self._update_overall_progress()
        self._update_status()

    def fail_format_export(self, format: ExportFormat, error_message: str, error_code: Optional[str] = None) -> None:
        """Mark a format export as failed."""
        if format in self.export_progress:
            self.export_progress[format].status = ExportStatus.FAILED
            self.export_progress[format].error_message = error_message
            self.export_progress[format].error_code = error_code

            if format not in self.failed_exports:
                self.failed_exports.append(format)

        self._update_overall_progress()
        self._update_status()

    def cancel_format_export(self, format: ExportFormat, reason: str = "User cancelled") -> None:
        """Cancel a specific format export."""
        if format in self.export_progress:
            self.export_progress[format].cancel_export(reason)

            if format not in self.cancelled_exports:
                self.cancelled_exports.append(format)

        self._update_overall_progress()
        self._update_status()

    def set_download_zip(self, zip_path: str) -> None:
        """Set the path for the download ZIP file."""
        self.download_zip_path = zip_path

    def _update_overall_progress(self) -> None:
        """Calculate overall progress across all formats."""
        if not self.formats:
            self.overall_progress = 0.0
            return

        total_progress = 0.0
        for format in self.formats:
            if format in self.export_progress:
                total_progress += self.export_progress[format].overall_progress
            else:
                # Format not yet started
                total_progress += 0.0

        self.overall_progress = total_progress / len(self.formats)

    def _update_status(self) -> None:
        """Update overall bulk export status."""
        if not self.formats:
            return

        all_completed = all(
            format in self.successful_exports for format in self.formats
        )
        all_failed = all(
            format in self.failed_exports for format in self.formats
        )
        all_cancelled = all(
            format in self.cancelled_exports for format in self.formats
        )

        any_running = any(
            export.status == ExportStatus.RUNNING for export in self.export_progress.values()
        )
        any_failed = len(self.failed_exports) > 0
        any_cancelled = len(self.cancelled_exports) > 0

        if all_completed:
            self.status = ExportStatus.COMPLETED
            self.completed_at = datetime.utcnow()
        elif all_failed:
            self.status = ExportStatus.FAILED
        elif all_cancelled:
            self.status = ExportStatus.CANCELLED
        elif any_running:
            self.status = ExportStatus.RUNNING
        elif any_failed and not any_running:
            self.status = ExportStatus.FAILED
        elif any_cancelled and not any_running:
            self.status = ExportStatus.CANCELLED

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of the bulk export progress."""
        return {
            "bulk_export_id": self.bulk_export_id,
            "presentation_id": self.presentation_id,
            "status": self.status.value,
            "overall_progress": round(self.overall_progress, 1),
            "total_formats": len(self.formats),
            "successful_exports": len(self.successful_exports),
            "failed_exports": len(self.failed_exports),
            "cancelled_exports": len(self.cancelled_exports),
            "running_exports": len([
                f for f, p in self.export_progress.items()
                if p.status == ExportStatus.RUNNING
            ]),
            "pending_exports": len([
                f for f, p in self.export_progress.items()
                if p.status == ExportStatus.PENDING
            ]),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion_time": (
                datetime.utcnow() + timedelta(seconds=self._get_estimated_total_remaining())
            ).isoformat() if self._get_estimated_total_remaining() else None,
            "download_zip_path": self.download_zip_path,
            "formats": {
                format.value: {
                    "status": progress.status.value,
                    "progress": progress.overall_progress,
                    "file_size_bytes": progress.file_size_bytes,
                    "filename": progress.filename,
                    "error_message": progress.error_message,
                    "current_step": progress.get_current_step_info(),
                }
                for format, progress in self.export_progress.items()
            }
        }

    def _get_estimated_total_remaining_seconds(self) -> Optional[float]:
        """Get estimated time remaining for the entire bulk export."""
        if not self.formats:
            return None

        total_remaining = 0.0
        for format in self.formats:
            if format in self.export_progress:
                total_remaining += self.export_progress[format].get_estimated_time_remaining_seconds() or 0.0
            else:
                # Estimate for not-yet-started formats
                total_remaining += 30.0  # Default estimate

        return total_remaining if total_remaining > 0 else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bulk_export_id": self.bulk_export_id,
            "presentation_id": self.presentation_id,
            "user_id": self.user_id,
            "formats": [f.value for f in self.formats],
            "status": self.status.value,
            "overall_progress": round(self.overall_progress, 1),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "successful_exports": [f.value for f in self.successful_exports],
            "failed_exports": [f.value for f in self.failed_exports],
            "cancelled_exports": [f.value for f in self.cancelled_exports],
            "error_message": self.error_message,
            "concurrent_exports": self.concurrent_exports,
            "download_zip_path": self.download_zip_path,
            "export_progress": {
                format.value: progress.to_dict()
                for format, progress in self.export_progress.items()
            },
            "progress_summary": self.get_progress_summary()
        }


# Export update message types
@dataclass
class ExportProgressUpdate:
    """A progress update message for export operations."""

    export_id: str
    format: Optional[ExportFormat] = None  # None for bulk updates
    bulk_export_id: Optional[str] = None
    progress: Optional[ExportFormatProgress] = None
    bulk_progress: Optional[BulkExportProgress] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    update_type: str = "export_progress"  # export_progress, format_complete, format_failed, export_complete, export_failed
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "export_id": self.export_id,
            "update_type": self.update_type,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
        }

        if self.format:
            data["format"] = self.format.value

        if self.bulk_export_id:
            data["bulk_export_id"] = self.bulk_export_id

        if self.progress:
            data["format_progress"] = self.progress.to_dict()

        if self.bulk_progress:
            data["bulk_progress"] = self.bulk_progress.to_dict()

        return data


@dataclass
class ExportAnalytics:
    """Analytics data for export operations."""

    export_id: str
    format: ExportFormat
    user_id: str
    presentation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ExportStatus = ExportStatus.PENDING
    file_size_bytes: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    quality_score: Optional[float] = None
    client_info: Dict[str, Any] = field(default_factory=dict)
    server_info: Dict[str, Any] = field(default_factory=dict)

    def complete_export(self, file_size_bytes: int, quality_score: Optional[float] = None) -> None:
        """Mark export as completed and calculate metrics."""
        self.end_time = datetime.utcnow()
        self.status = ExportStatus.COMPLETED
        self.file_size_bytes = file_size_bytes
        self.quality_score = quality_score

        if self.start_time:
            self.processing_time_seconds = (self.end_time - self.start_time).total_seconds()

    def fail_export(self, error_code: str) -> None:
        """Mark export as failed."""
        self.end_time = datetime.utcnow()
        self.status = ExportStatus.FAILED
        self.error_code = error_code

        if self.start_time:
            self.processing_time_seconds = (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analytics storage."""
        return {
            "export_id": self.export_id,
            "format": self.format.value,
            "user_id": self.user_id,
            "presentation_id": self.presentation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "file_size_bytes": self.file_size_bytes,
            "processing_time_seconds": self.processing_time_seconds,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "quality_score": self.quality_score,
            "client_info": self.client_info,
            "server_info": self.server_info,
        }