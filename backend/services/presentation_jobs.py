"""Background job management for presentation generation.

This module provides async job execution for presentation generation
using FastAPI BackgroundTasks and now uses database-backed job tracking.

The legacy in-memory implementation has been migrated to use database persistence
for better reliability and recovery capabilities.
"""

import logging

# Import the database-backed implementation
from .presentation_jobs_persistent import (
    PresentationJobManager,
    PresentationJob,
    JobStatus,
    JobPriority,
    get_job_manager,
    create_presentation_job,
    get_presentation_job_status,
    initialize_job_system,
)

# Re-export for backward compatibility
__all__ = [
    "PresentationJobManager",
    "PresentationJob",
    "JobStatus",
    "JobPriority",
    "get_job_manager",
    "create_presentation_job",
    "get_presentation_job_status",
    "initialize_job_system",
]

logger = logging.getLogger(__name__)

# This file now serves as a backward-compatible wrapper that imports the persistent implementation
# All functionality is delegated to the database-backed version in presentation_jobs_persistent.py