"""Standardized ingestion response schema for harmonizing ingestion endpoints"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json


class IngestionStatus(str):
    """Standardized ingestion status values"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class IngestionResponse:
    """Standardized ingestion response envelope"""
    status: str  # "success", "error", "partial", "pending"
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# Helper functions for creating common response types


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create a successful ingestion response"""
    return IngestionResponse(
        status=IngestionStatus.SUCCESS,
        message=message,
        data=data,
        meta=meta
    )


def create_error_response(
    message: str,
    errors: Optional[List[Dict[str, Any]]] = None,
    data: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create an error ingestion response"""
    return IngestionResponse(
        status=IngestionStatus.ERROR,
        message=message,
        data=data,
        errors=errors,
        meta=meta
    )


def create_partial_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create a partial success ingestion response (e.g., batch operations)"""
    return IngestionResponse(
        status=IngestionStatus.PARTIAL,
        message=message,
        data=data,
        errors=errors,
        meta=meta
    )


def create_pending_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create a pending ingestion response (e.g., background processing)"""
    return IngestionResponse(
        status=IngestionStatus.PENDING,
        message=message,
        data=data,
        meta=meta
    )


# Batch operation helpers for common patterns


def create_batch_success_response(
    success_count: int,
    total_count: int,
    message: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create a successful batch ingestion response"""
    if message is None:
        message = f"Successfully processed {success_count} of {total_count} items"

    batch_data = {
        "success_count": success_count,
        "total_count": total_count,
        "failure_count": total_count - success_count
    }
    if data:
        batch_data.update(data)

    return create_success_response(
        message=message,
        data=batch_data,
        meta={"operation_type": "batch"}
    )


def create_batch_partial_response(
    success_count: int,
    failure_count: int,
    total_count: int,
    errors: Optional[List[Dict[str, Any]]] = None,
    message: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> IngestionResponse:
    """Create a partial success batch ingestion response"""
    if message is None:
        message = f"Partially completed: {success_count} succeeded, {failure_count} failed out of {total_count} total"

    batch_data = {
        "success_count": success_count,
        "failure_count": failure_count,
        "total_count": total_count
    }
    if data:
        batch_data.update(data)

    return create_partial_response(
        message=message,
        data=batch_data,
        errors=errors,
        meta={"operation_type": "batch"}
    )


# Utility to wrap existing responses


def wrap_existing_response(
    existing_data: Dict[str, Any],
    status: str = IngestionStatus.SUCCESS,
    message: Optional[str] = None
) -> IngestionResponse:
    """
    Wrap existing response data in the standardized ingestion envelope

    Args:
        existing_data: The existing response data to wrap
        status: The ingestion status
        message: Optional message override

    Returns:
        Standardized IngestionResponse
    """
    if message is None:
        if status == IngestionStatus.SUCCESS:
            message = "Operation completed successfully"
        elif status == IngestionStatus.ERROR:
            message = "Operation failed"
        elif status == IngestionStatus.PARTIAL:
            message = "Operation partially completed"
        elif status == IngestionStatus.PENDING:
            message = "Operation is pending"
        else:
            message = "Operation processed"

    return IngestionResponse(
        status=status,
        message=message,
        data=existing_data
    )


# HTTP status mapping
def get_http_status_for_ingestion_status(ingestion_status: str) -> int:
    """Map ingestion status to appropriate HTTP status code"""
    if ingestion_status == IngestionStatus.SUCCESS:
        return 200
    elif ingestion_status == IngestionStatus.ERROR:
        return 400
    elif ingestion_status == IngestionStatus.PARTIAL:
        return 207  # Multi-Status
    elif ingestion_status == IngestionStatus.PENDING:
        return 202  # Accepted
    else:
        return 200


# Error handling helpers


def create_file_error_response(
    error_message: str,
    file_path: Optional[str] = None,
    error_code: Optional[str] = None
) -> IngestionResponse:
    """Create a standardized file processing error response"""
    errors = [{"message": error_message}]
    if file_path:
        errors[0]["file_path"] = file_path
    if error_code:
        errors[0]["code"] = error_code

    return create_error_response(
        message=f"File processing failed: {error_message}",
        errors=errors,
        meta={"error_type": "file_processing"}
    )


def create_validation_error_response(
    validation_errors: List[Dict[str, Any]],
    message: Optional[str] = None
) -> IngestionResponse:
    """Create a standardized validation error response"""
    if message is None:
        message = "Validation failed"

    return create_error_response(
        message=message,
        errors=validation_errors,
        meta={"error_type": "validation"}
    )