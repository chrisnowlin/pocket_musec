"""Comprehensive error handling for presentation generation system.

This module defines specific error types and user-friendly messages
for different failure scenarios in the presentation generation pipeline.
"""

import logging
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PresentationErrorCode(str, Enum):
    """Unique error codes for presentation generation failures."""

    # Lesson-related errors
    LESSON_NOT_FOUND = "lesson_not_found"
    LESSON_ACCESS_DENIED = "lesson_access_denied"
    LESSON_INVALID_FORMAT = "lesson_invalid_format"
    LESSON_PARSE_FAILED = "lesson_parse_failed"

    # LLM-related errors
    LLM_TIMEOUT = "llm_timeout"
    LLM_RATE_LIMITED = "llm_rate_limited"
    LLM_UNAVAILABLE = "llm_unavailable"
    LLM_QUOTA_EXCEEDED = "llm_quota_exceeded"
    LLM_CONTENT_FILTERED = "llm_content_filtered"
    LLM_INVALID_RESPONSE = "llm_invalid_response"

    # Export-related errors
    EXPORT_FAILED = "export_failed"
    EXPORT_PPTX_FAILED = "export_pptx_failed"
    EXPORT_PDF_FAILED = "export_pdf_failed"
    EXPORT_JSON_FAILED = "export_json_failed"
    EXPORT_MARKDOWN_FAILED = "export_markdown_failed"
    EXPORT_PERMISSION_DENIED = "export_permission_denied"
    EXPORT_STORAGE_FAILED = "export_storage_failed"

    # Job system errors
    JOB_NOT_FOUND = "job_not_found"
    JOB_ACCESS_DENIED = "job_access_denied"
    JOB_TIMEOUT = "job_timeout"
    JOB_CANCELLED = "job_cancelled"
    JOB_ALREADY_RUNNING = "job_already_running"

    # Validation errors
    VALIDATION_FAILED = "validation_failed"
    INVALID_STYLE = "invalid_style"
    INVALID_TIMEOUT = "invalid_timeout"
    INVALID_EXPORT_FORMAT = "invalid_export_format"

    # Style-related errors
    STYLE_NOT_FOUND = "style_not_found"
    STYLE_ACCESS_DENIED = "style_access_denied"

    # System errors
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


@dataclass
class PresentationError(Exception):
    """Structured error information for presentation generation failures."""

    code: PresentationErrorCode
    user_message: str
    technical_message: str
    retry_recommended: bool = False
    retry_after_seconds: Optional[int] = None
    escalation_required: bool = False
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Initialize base Exception with a user-facing message so it can be raised normally
        super().__init__(self.user_message)

    @classmethod
    def lesson_not_found(cls, lesson_id: str) -> "PresentationError":
        """Error when lesson cannot be found."""
        return cls(
            code=PresentationErrorCode.LESSON_NOT_FOUND,
            user_message=f"Lesson '{lesson_id}' could not be found. Please check the lesson ID and try again.",
            technical_message=f"Lesson with ID {lesson_id} not found in database",
            retry_recommended=False,
        )

    @classmethod
    def lesson_access_denied(cls, lesson_id: str) -> "PresentationError":
        """Error when user doesn't have access to lesson."""
        return cls(
            code=PresentationErrorCode.LESSON_ACCESS_DENIED,
            user_message=f"You don't have permission to access lesson '{lesson_id}'. Please verify your access rights.",
            technical_message=f"User access denied for lesson {lesson_id}",
            retry_recommended=False,
        )

    @classmethod
    def llm_timeout(cls, timeout_seconds: int) -> "PresentationError":
        """Error when LLM operations timeout."""
        return cls(
            code=PresentationErrorCode.LLM_TIMEOUT,
            user_message=f"The presentation generation took too long. Try again with a longer timeout or disable AI polishing for faster results.",
            technical_message=f"LLM operation timed out after {timeout_seconds} seconds",
            retry_recommended=True,
            retry_after_seconds=5,
        )

    @classmethod
    def llm_unavailable(cls) -> "PresentationError":
        """Error when LLM service is unavailable."""
        return cls(
            code=PresentationErrorCode.LLM_UNAVAILABLE,
            user_message="AI polishing service is temporarily unavailable. You can continue with basic presentation generation or try again later.",
            technical_message="LLM service is not responding",
            retry_recommended=True,
            retry_after_seconds=30,
        )

    @classmethod
    def llm_rate_limited(cls) -> "PresentationError":
        """Error when rate limited by LLM service."""
        return cls(
            code=PresentationErrorCode.LLM_RATE_LIMITED,
            user_message="Too many requests to the AI service. Please wait a few moments before trying again.",
            technical_message="LLM service rate limit exceeded",
            retry_recommended=True,
            retry_after_seconds=60,
        )

    @classmethod
    def export_failed(cls, format: str, technical_details: str) -> "PresentationError":
        """Error when export generation fails."""
        return cls(
            code=getattr(
                PresentationErrorCode,
                f"export_{format.upper()}_FAILED",
                PresentationErrorCode.INTERNAL_ERROR,
            ),
            user_message=f"Failed to generate {format.upper()} export. Please try again or contact support if the issue persists.",
            technical_message=f"{format.upper()} export failed: {technical_details}",
            retry_recommended=True,
            retry_after_seconds=10,
        )

    @classmethod
    def job_timed_out(cls, job_id: str) -> "PresentationError":
        """Error when job execution times out."""
        return cls(
            code=PresentationErrorCode.JOB_TIMEOUT,
            user_message="Presentation generation is taking too long. The job has been cancelled. Try with simpler content or a longer timeout.",
            technical_message=f"Job {job_id} exceeded maximum execution time",
            retry_recommended=True,
            retry_after_seconds=15,
        )

    @classmethod
    def database_error(cls, operation: str) -> "PresentationError":
        """Error when database operation fails."""
        return cls(
            code=PresentationErrorCode.DATABASE_ERROR,
            user_message="A database error occurred while saving your presentation. Please try again.",
            technical_message=f"Database operation failed during {operation}",
            retry_recommended=True,
            retry_after_seconds=5,
        )

    @classmethod
    def permission_denied(cls, action: str) -> "PresentationError":
        """Error when permission is denied."""
        return cls(
            code=PresentationErrorCode.PERMISSION_DENIED,
            user_message=f"You don't have permission to {action}. Please contact your administrator.",
            technical_message=f"Permission denied for action: {action}",
            retry_recommended=False,
        )

    @classmethod
    def validation_failed(cls, field: str, value: Any) -> "PresentationError":
        """Error when validation fails."""
        return cls(
            code=PresentationErrorCode.VALIDATION_FAILED,
            user_message=f"Invalid value for {field}: {value}. Please check your input and try again.",
            technical_message=f"Validation failed for field '{field}' with value '{value}'",
            retry_recommended=False,
        )

    @classmethod
    def lesson_parse_failed(cls, details: str) -> "PresentationError":
        """Error when lesson parsing fails."""
        return cls(
            code=PresentationErrorCode.LESSON_PARSE_FAILED,
            user_message="Unable to process lesson content. Please check the lesson format and content.",
            technical_message=f"Lesson parsing failed: {details}",
            retry_recommended=True,
            retry_after_seconds=5,
        )

    @classmethod
    def service_unavailable(cls, service_name: str) -> "PresentationError":
        """Error when external service is unavailable."""
        return cls(
            code=PresentationErrorCode.SERVICE_UNAVAILABLE,
            user_message=f"The {service_name} service is temporarily unavailable. Please try again later.",
            technical_message=f"External service {service_name} is not available",
            retry_recommended=True,
            retry_after_seconds=30,
        )

    @classmethod
    def internal_error(cls, message: str) -> "PresentationError":
        """Error for unexpected internal failures."""
        return cls(
            code=PresentationErrorCode.INTERNAL_ERROR,
            user_message="An unexpected error occurred. Please try again or contact support if the problem persists.",
            technical_message=f"Internal error: {message}",
            retry_recommended=True,
            retry_after_seconds=10,
            escalation_required=True,
        )

    @classmethod
    def invalid_style(cls, message: str) -> "PresentationError":
        """Error when style configuration is invalid."""
        return cls(
            code=PresentationErrorCode.INVALID_STYLE,
            user_message=f"Invalid style configuration: {message}",
            technical_message=f"Style validation failed: {message}",
            retry_recommended=False,
        )

    @classmethod
    def style_not_found(cls, style_id: str) -> "PresentationError":
        """Error when style cannot be found."""
        return cls(
            code=PresentationErrorCode.STYLE_NOT_FOUND,
            user_message=f"Style '{style_id}' could not be found. Please check the style ID and try again.",
            technical_message=f"Style with ID {style_id} not found",
            retry_recommended=False,
        )

    @classmethod
    def style_access_denied(cls, style_id: str) -> "PresentationError":
        """Error when user doesn't have access to style."""
        return cls(
            code=PresentationErrorCode.STYLE_ACCESS_DENIED,
            user_message=f"You don't have permission to access style '{style_id}'. Please verify your access rights.",
            technical_message=f"User access denied for style {style_id}",
            retry_recommended=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "code": self.code.value,
            "user_message": self.user_message,
            "technical_message": self.technical_message,
            "retry_recommended": self.retry_recommended,
            "retry_after_seconds": self.retry_after_seconds,
            "escalation_required": self.escalation_required,
            "context": self.context,
        }


class PresentationErrorLogger:
    """Centralized error logging with context and severity tracking."""

    @staticmethod
    def log_error(error: PresentationError, context: Optional[Dict[str, Any]] = None):
        """Log error with appropriate severity and context."""
        log_context = {**(error.context or {}), **(context or {})}

        log_data = {
            "error_code": error.code.value,
            "technical_message": error.technical_message,
            "user_message": error.user_message,
            "context": log_context,
        }

        # Determine log level based on error severity
        if error.escalation_required:
            logger.critical(
                f"Critical presentation error: {error.code.value}", extra=log_data
            )
        elif error.code in [
            PresentationErrorCode.DATABASE_ERROR,
            PresentationErrorCode.SERVICE_UNAVAILABLE,
        ]:
            logger.error(f"Presentation error: {error.code.value}", extra=log_data)
        elif error.code in [
            PresentationErrorCode.LLM_TIMEOUT,
            PresentationErrorCode.LLM_RATE_LIMITED,
            PresentationErrorCode.EXPORT_FAILED,
        ]:
            logger.warning(f"Presentation warning: {error.code.value}", extra=log_data)
        else:
            logger.info(f"Presentation info error: {error.code.value}", extra=log_data)

    @staticmethod
    def log_recovery_attempt(
        error: PresentationError, action: str, context: Optional[Dict[str, Any]] = None
    ):
        """Log recovery attempts for monitoring."""
        logger.info(
            f"Attempting recovery from {error.code.value}: {action}",
            extra={
                "original_error": error.code.value,
                "recovery_action": action,
                "context": context or {},
            },
        )


class ErrorRecoveryStrategy:
    """Strategies for recovering from different types of errors."""

    @staticmethod
    def get_recovery_actions(error: PresentationError) -> list[str]:
        """Get recommended recovery actions for an error."""
        actions = []

        if error.retry_recommended:
            if error.retry_after_seconds:
                actions.append(f"Retry in {error.retry_after_seconds} seconds")
            else:
                actions.append("Retry the operation")

        if error.code in [
            PresentationErrorCode.LLM_TIMEOUT,
            PresentationErrorCode.LLM_UNAVAILABLE,
        ]:
            actions.extend(
                [
                    "Disable AI polishing for faster generation",
                    "Reduce timeout value",
                    "Try with simpler lesson content",
                ]
            )

        if error.code in [
            PresentationErrorCode.EXPORT_PPTX_FAILED,
            PresentationErrorCode.EXPORT_PDF_FAILED,
        ]:
            actions.extend(
                [
                    "Try alternative export format (JSON or Markdown)",
                    "Check disk space and permissions",
                    "Contact support for file format issues",
                ]
            )

        if error.code in [PresentationErrorCode.DATABASE_ERROR]:
            actions.extend(
                [
                    "Check your internet connection",
                    "Try refreshing the page",
                    "Contact administrator if issue persists",
                ]
            )

        if error.escalation_required:
            actions.append("Contact technical support")

        return actions


def create_error_from_exception(
    exc: Exception, context: Optional[Dict[str, Any]] = None
) -> PresentationError:
    """Create PresentationError from generic exception."""
    context = context or {}

    # Network/timeout errors
    if "timeout" in str(exc).lower():
        return PresentationError.llm_timeout(context.get("timeout_seconds", 30))

    if "connection" in str(exc).lower() or "network" in str(exc).lower():
        return PresentationError.service_unavailable("Network")

    # Database errors
    if "database" in str(exc).lower() or "sqlite" in str(exc).lower():
        return PresentationError.database_error(context.get("operation", "unknown"))

    # Import errors for exports
    if "ModuleNotFoundError" in str(type(exc).__name__):
        missing_module = getattr(exc, "name", "unknown")
        format_mapping = {"pptx": "pptx", "reportlab": "pdf"}
        export_format = format_mapping.get(missing_module, "unknown")
        return PresentationError.export_failed(
            export_format, f"Missing dependency: {missing_module}"
        )

    # Permission errors
    if "permission" in str(exc).lower():
        return PresentationError.permission_denied(
            context.get("action", "access resource")
        )

    # Generic internal error
    return PresentationError.internal_error(str(exc))
