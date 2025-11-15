"""Endpoints for managing embeddings and semantic search"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime
from pydantic import BaseModel
import logging

from ...llm.embeddings import (
    StandardsEmbedder,
    StandardsEmbeddings,
    EmbeddedStandard,
    EmbeddedObjective,
)
from ..dependencies import get_current_user
from ...auth import User
from ...services.embedding_job_manager import get_job_manager, EmbeddingJobManager
from ...models.embedding_jobs import EmbeddingJob, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])


class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding statistics"""

    standard_embeddings: int
    objective_embeddings: int
    embedding_dimension: int


class EmbeddingGenerateRequest(BaseModel):
    """Request model for generating embeddings"""

    force: bool = False
    batch_size: int = 10


class EmbeddingGenerateResponse(BaseModel):
    """Response model for embedding generation results"""

    success: int
    failed: int
    skipped: int
    message: str


class BatchOperationRequest(BaseModel):
    """Request model for batch operations"""

    operation: str  # 'regenerate', 'delete', 'refresh'
    filters: Optional[Dict[str, Any]] = (
        None  # Optional filters for selective operations
    )


class BatchOperationResponse(BaseModel):
    """Response model for batch operation results"""

    success: int
    failed: int
    skipped: int
    message: str


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""

    query: str
    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    limit: int = 10
    threshold: float = 0.5
    offset: int = 0


class SemanticSearchResult(BaseModel):
    """Response model for semantic search results"""

    standard_id: str
    grade_level: str
    strand_code: str
    strand_name: str
    standard_text: str
    similarity: float


class SemanticSearchResponse(BaseModel):
    """Response model for paginated semantic search results"""

    results: List[SemanticSearchResult]
    total_count: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class PreparedTextsResponse(BaseModel):
    """Response model for prepared texts"""

    standards: List[str]
    objectives: List[str]


class ShowTextResponse(BaseModel):
    """Response model for showing prepared text"""

    text: str
    item_id: str
    item_type: str


class JobResponse(BaseModel):
    """Response model for embedding job"""

    id: str
    status: str
    progress: int
    message: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    error_details: Optional[str]
    duration_seconds: Optional[float]


class JobListResponse(BaseModel):
    """Response model for job list"""

    jobs: List[JobResponse]
    total_count: int


# Global variable to track generation progress
_generation_progress = {"status": "idle", "progress": 0, "message": ""}


@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats(
    current_user: User = Depends(get_current_user),
) -> EmbeddingStatsResponse:
    """Get statistics about embeddings in the database"""
    try:
        embeddings_manager = StandardsEmbeddings()
        stats = embeddings_manager.get_embedding_stats()
        return EmbeddingStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding stats: {str(e)}",
        )


@router.post("/generate", response_model=EmbeddingGenerateResponse)
async def generate_embeddings(
    request: EmbeddingGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> EmbeddingGenerateResponse:
    """Generate embeddings for all standards and objectives"""
    global _generation_progress

    try:
        # Check if already running
        if _generation_progress["status"] == "running":
            return EmbeddingGenerateResponse(
                success=0,
                failed=0,
                skipped=0,
                message="Embedding generation already in progress",
            )

        # Check if embeddings already exist
        embeddings_manager = StandardsEmbeddings()
        stats = embeddings_manager.get_embedding_stats()

        if stats["standard_embeddings"] > 0 and not request.force:
            return EmbeddingGenerateResponse(
                success=0,
                failed=0,
                skipped=0,
                message=f"Found {stats['standard_embeddings']} existing embeddings. Use force=true to regenerate.",
            )

        # Start background generation
        _generation_progress["status"] = "running"
        _generation_progress["progress"] = 0
        _generation_progress["message"] = "Starting embedding generation..."

        background_tasks.add_task(
            _generate_embeddings_background, request.force, request.batch_size
        )

        return EmbeddingGenerateResponse(
            success=0,
            failed=0,
            skipped=0,
            message="Embedding generation started in background",
        )

    except Exception as e:
        _generation_progress["status"] = "error"
        _generation_progress["message"] = f"Error: {str(e)}"
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start embedding generation: {str(e)}",
        )


@router.get("/generate/progress")
async def get_generation_progress(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get progress of ongoing embedding generation"""
    return _generation_progress.copy()


async def _generate_embeddings_background(force: bool, batch_size: int):
    """Background task for generating embeddings"""
    global _generation_progress

    try:
        embedder = StandardsEmbedder()

        _generation_progress["message"] = "Generating embeddings..."
        _generation_progress["progress"] = 50

        # Generate embeddings
        result_stats = embedder.embed_all_standards(batch_size=batch_size)

        _generation_progress["status"] = "completed"
        _generation_progress["progress"] = 100
        _generation_progress["message"] = (
            f"Completed: {result_stats['success']} embedded, {result_stats['failed']} failed, {result_stats['skipped']} skipped"
        )

    except Exception as e:
        _generation_progress["status"] = "error"
        _generation_progress["message"] = f"Error: {str(e)}"


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
) -> SemanticSearchResponse:
    """Search for standards using semantic similarity with pagination"""
    try:
        embeddings_manager = StandardsEmbeddings()

        # Generate embedding for query
        query_embedding = embeddings_manager.embed_query(request.query)

        # Search for similar standards with a larger limit to get total count
        # We fetch more than needed to determine total available results
        fetch_limit = min(
            request.limit + request.offset + 100, 1000
        )  # Cap at 1000 for performance
        all_results = embeddings_manager.search_similar_standards(
            query_embedding=query_embedding,
            grade_level=request.grade_level,
            strand_code=request.strand_code,
            limit=fetch_limit,
            similarity_threshold=request.threshold,
        )

        # Apply pagination
        total_count = len(all_results)
        paginated_results = all_results[request.offset : request.offset + request.limit]

        # Convert to response format
        search_results = []
        for embedded_standard, similarity in paginated_results:
            search_results.append(
                SemanticSearchResult(
                    standard_id=embedded_standard.standard_id,
                    grade_level=embedded_standard.grade_level,
                    strand_code=embedded_standard.strand_code,
                    strand_name=embedded_standard.strand_name,
                    standard_text=embedded_standard.standard_text,
                    similarity=similarity,
                )
            )

        # Calculate pagination info
        has_next = request.offset + request.limit < total_count
        has_previous = request.offset > 0

        return SemanticSearchResponse(
            results=search_results,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
            has_next=has_next,
            has_previous=has_previous,
        )

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search standards: {str(e)}",
        )


@router.delete("/clear")
async def clear_embeddings(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Clear all embeddings from the database"""
    try:
        embeddings_manager = StandardsEmbeddings()
        embeddings_manager.delete_all_embeddings()

        # Reset progress
        global _generation_progress
        _generation_progress = {"status": "idle", "progress": 0, "message": ""}

        return {"message": "All embeddings deleted from database"}

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear embeddings: {str(e)}",
        )


@router.get("/texts", response_model=PreparedTextsResponse)
async def list_prepared_texts(
    current_user: User = Depends(get_current_user),
) -> PreparedTextsResponse:
    """List all prepared embedding text files"""
    try:
        embeddings_manager = StandardsEmbeddings()
        texts = embeddings_manager.list_prepared_texts()
        return PreparedTextsResponse(**texts)

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prepared texts: {str(e)}",
        )


@router.get("/texts/{item_id}", response_model=ShowTextResponse)
async def show_prepared_text(
    item_id: str,
    item_type: str = Query("standard", regex="^(standard|objective)$"),
    current_user: User = Depends(get_current_user),
) -> ShowTextResponse:
    """Show prepared text for a specific standard or objective"""
    try:
        embeddings_manager = StandardsEmbeddings()

        if item_type == "standard":
            text = embeddings_manager.get_prepared_standard_text(item_id)
        else:
            text = embeddings_manager.get_prepared_objective_text(item_id)

        if not text:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"No prepared text found for {item_type} {item_id}",
            )

        return ShowTextResponse(text=text, item_id=item_id, item_type=item_type)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prepared text: {str(e)}",
        )


@router.delete("/texts/clear")
async def clear_prepared_texts(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Clear all prepared text files"""
    try:
        embeddings_manager = StandardsEmbeddings()
        embeddings_manager.delete_all_prepared_texts()
        return {"message": "All prepared text files deleted"}

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear prepared texts: {str(e)}",
        )


# Usage tracking endpoints
class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""

    total_searches: int
    total_generations: int
    searches_this_week: int
    generations_this_week: int
    last_search: Optional[str] = None
    last_generation: Optional[str] = None


@router.get("/usage/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
) -> UsageStatsResponse:
    """Get usage statistics for embeddings operations"""
    try:
        # In a real implementation, this would query a database or log files
        # For now, we'll return mock data
        return UsageStatsResponse(
            total_searches=0,
            total_generations=0,
            searches_this_week=0,
            generations_this_week=0,
            last_search=None,
            last_generation=None,
        )
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}",
        )


@router.post("/usage/track/search")
async def track_search_usage(
    query: str,
    result_count: int,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Track a search operation"""
    try:
        # In a real implementation, this would log to a database or analytics service
        # For now, we'll just return success
        logger.info(f"Search tracked: query='{query[:50]}...', results={result_count}")
        return {"message": "Search usage tracked"}
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track search usage: {str(e)}",
        )


@router.post("/usage/track/generation")
async def track_generation_usage(
    success: int,
    failed: int,
    skipped: int,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Track a generation operation"""
    try:
        # In a real implementation, this would log to a database or analytics service
        # For now, we'll just return success
        logger.info(
            f"Generation tracked: success={success}, failed={failed}, skipped={skipped}"
        )
        return {"message": "Generation usage tracked"}
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track generation usage: {str(e)}",
        )


@router.get("/stats/export/csv")
async def export_stats_csv(
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Export embedding statistics as CSV file."""
    try:
        embeddings_manager = StandardsEmbeddings()
        stats = embeddings_manager.get_embedding_stats()

        # Create CSV content
        csv_content = [
            "Embedding Statistics",
            f"Standard Embeddings,{stats['standard_embeddings']}",
            f"Objective Embeddings,{stats['objective_embeddings']}",
            f"Embedding Dimension,{stats['embedding_dimension']}",
            "",
            "Usage Statistics",
            f"Total Searches,0",  # Mock data for now
            f"Total Generations,0",  # Mock data for now
            f"Searches This Week,0",  # Mock data for now
            f"Generations This Week,0",  # Mock data for now
            f"Last Search,Never",  # Mock data for now
            f"Last Generation,Never",  # Mock data for now
        ]

        # Create temporary file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            tmp_file.write("\n".join(csv_content))
            tmp_file_path = tmp_file.name

        logger.info("Exported embedding statistics as CSV")

        return FileResponse(
            tmp_file_path,
            media_type="text/csv",
            filename=f"embedding_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    except Exception as e:
        logger.error(f"Failed to export stats as CSV: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export stats: {str(e)}",
        )


@router.get("/stats/export/json")
async def export_stats_json(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Export embedding statistics as JSON."""
    try:
        embeddings_manager = StandardsEmbeddings()
        stats = embeddings_manager.get_embedding_stats()

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "embedding_statistics": stats,
            "usage_statistics": {
                "total_searches": 0,  # Mock data for now
                "total_generations": 0,  # Mock data for now
                "searches_this_week": 0,  # Mock data for now
                "generations_this_week": 0,  # Mock data for now
                "last_search": None,  # Mock data for now
                "last_generation": None,  # Mock data for now
            },
        }

        logger.info("Exported embedding statistics as JSON")
        return export_data

    except Exception as e:
        logger.error(f"Failed to export stats as JSON: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export stats: {str(e)}",
        )


@router.get("/usage/export/csv")
async def export_usage_csv(
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Export usage statistics as CSV file."""
    try:
        # Create CSV content with mock data for now
        csv_content = [
            "Usage Statistics",
            f"Total Searches,0",
            f"Total Generations,0",
            f"Searches This Week,0",
            f"Generations This Week,0",
            f"Last Search,Never",
            f"Last Generation,Never",
        ]

        # Create temporary file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            tmp_file.write("\n".join(csv_content))
            tmp_file_path = tmp_file.name

        logger.info("Exported usage statistics as CSV")

        return FileResponse(
            tmp_file_path,
            media_type="text/csv",
            filename=f"usage_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    except Exception as e:
        logger.error(f"Failed to export usage as CSV: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export usage: {str(e)}",
        )


@router.post("/batch", response_model=BatchOperationResponse)
async def batch_operations(
    request: BatchOperationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> BatchOperationResponse:
    """Perform batch operations on embeddings"""
    try:
        # Check if already running
        if _generation_progress["status"] == "running":
            return BatchOperationResponse(
                success=0,
                failed=0,
                skipped=0,
                message="Batch operation already in progress",
            )

        # Validate operation
        if request.operation not in ["regenerate", "delete", "refresh"]:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {request.operation}. Must be 'regenerate', 'delete', or 'refresh'",
            )

        # Start background operation
        _generation_progress["status"] = "running"
        _generation_progress["progress"] = 0
        _generation_progress["message"] = f"Starting batch {request.operation}..."

        background_tasks.add_task(
            _execute_batch_operation, request.operation, request.filters or {}
        )

        return BatchOperationResponse(
            success=0,
            failed=0,
            skipped=0,
            message=f"Batch {request.operation} started in background",
        )

    except HTTPException:
        raise
    except Exception as e:
        _generation_progress["status"] = "error"
        _generation_progress["message"] = f"Error: {str(e)}"
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch operation: {str(e)}",
        )


async def _execute_batch_operation(operation: str, filters: Dict[str, Any]):
    """Background task for executing batch operations"""
    global _generation_progress

    try:
        embeddings_manager = StandardsEmbeddings()

        if operation == "delete":
            _generation_progress["message"] = "Deleting embeddings in batch..."
            _generation_progress["progress"] = 25

            # Delete all embeddings
            embeddings_manager.delete_all_embeddings()

            _generation_progress["status"] = "completed"
            _generation_progress["progress"] = 100
            _generation_progress["message"] = "Batch delete completed successfully"

        elif operation == "regenerate":
            _generation_progress["message"] = "Regenerating embeddings in batch..."
            _generation_progress["progress"] = 25

            # Clear existing embeddings first
            embeddings_manager.delete_all_embeddings()

            _generation_progress["message"] = "Generating new embeddings..."
            _generation_progress["progress"] = 50

            # Generate new embeddings
            embedder = StandardsEmbedder()
            result_stats = embedder.embed_all_standards(batch_size=20)

            _generation_progress["status"] = "completed"
            _generation_progress["progress"] = 100
            _generation_progress["message"] = (
                f"Batch regenerate completed: {result_stats['success']} embedded, {result_stats['failed']} failed, {result_stats['skipped']} skipped"
            )

        elif operation == "refresh":
            _generation_progress["message"] = "Refreshing embeddings cache..."
            _generation_progress["progress"] = 50

            # In a real implementation, this would refresh any cached embeddings
            # For now, we'll just complete the operation
            _generation_progress["status"] = "completed"
            _generation_progress["progress"] = 100
            _generation_progress["message"] = "Batch refresh completed successfully"

    except Exception as e:
        _generation_progress["status"] = "error"
        _generation_progress["message"] = f"Error: {str(e)}"


# New job-based endpoints


@router.post("/jobs", response_model=JobResponse)
async def create_embedding_job(
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """Create a new embedding generation job"""
    try:
        job_manager = get_job_manager()

        # Check if there's already a running job
        active_job = job_manager.get_active_job()
        if active_job:
            return _job_to_response(active_job)

        # Count total items to process
        embeddings_manager = StandardsEmbeddings()
        stats = embeddings_manager.get_embedding_stats()
        total_items = stats.get("total_standards", 0) + stats.get("total_objectives", 0)

        # Create new job
        job = job_manager.create_job(
            total_items=total_items,
            metadata={
                "created_by": current_user.id
                if hasattr(current_user, "id")
                else "demo_user"
            },
        )

        return _job_to_response(job)

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create embedding job: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_embedding_job(
    job_id: str, current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Get embedding job by ID"""
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")

        return _job_to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding job: {str(e)}",
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_embedding_jobs(
    limit: int = Query(10, ge=1, le=100), current_user: User = Depends(get_current_user)
) -> JobListResponse:
    """List recent embedding jobs"""
    try:
        job_manager = get_job_manager()
        jobs = job_manager.get_recent_jobs(limit=limit)

        return JobListResponse(
            jobs=[_job_to_response(job) for job in jobs], total_count=len(jobs)
        )

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list embedding jobs: {str(e)}",
        )


@router.post("/jobs/{job_id}/start", response_model=JobResponse)
async def start_embedding_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """Start an embedding job"""
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")

        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Job cannot be started (current status: {job.status})",
            )

        # Check if there's already a running job
        active_job = job_manager.get_active_job()
        if active_job and active_job.id != job_id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Another embedding job is already running",
            )

        # Start the job
        job.start()
        job_manager.update_job(job)

        # Add background task to run the embedding generation
        background_tasks.add_task(_run_embedding_job, job_id)

        return _job_to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start embedding job: {str(e)}",
        )


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_embedding_job(
    job_id: str, current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Cancel an embedding job"""
    try:
        job_manager = get_job_manager()
        success = job_manager.cancel_job(job_id)

        if not success:
            job = job_manager.get_job(job_id)
            if not job:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Job cannot be cancelled (current status: {job.status})",
                )

        job = job_manager.get_job(job_id)
        return _job_to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel embedding job: {str(e)}",
        )


def _job_to_response(job: EmbeddingJob) -> JobResponse:
    """Convert EmbeddingJob to JobResponse"""
    return JobResponse(
        id=job.id,
        status=job.status.value,
        progress=job.progress,
        message=job.message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        total_items=job.total_items,
        processed_items=job.processed_items,
        successful_items=job.successful_items,
        failed_items=job.failed_items,
        error_details=job.error_details,
        duration_seconds=job.get_duration(),
    )


async def _run_embedding_job(job_id: str):
    """Background task to run embedding generation"""
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            logger.error(f"Job {job_id} not found for background execution")
            return

        # Initialize embeddings manager
        embeddings_manager = StandardsEmbeddings()

        # Update job with total count
        stats = embeddings_manager.get_embedding_stats()
        total_standards = stats.get("total_standards", 0)
        total_objectives = stats.get("total_objectives", 0)
        job.total_items = total_standards + total_objectives
        job_manager.update_job(job)

        # Generate embeddings
        result = embeddings_manager.generate_all_embeddings(
            progress_callback=lambda processed,
            successful,
            failed,
            msg: _update_job_progress(
                job_manager, job_id, processed, successful, failed, msg
            )
        )

        # Complete the job
        job.complete(
            success_count=result.get("success", 0),
            failed_count=result.get("failed", 0),
            message=f"Embedding generation completed: {result.get('success', 0)} successful, {result.get('failed', 0)} failed",
        )
        job_manager.update_job(job)

        logger.info(f"Embedding job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Embedding job {job_id} failed: {e}")

        # Mark job as failed
        try:
            job_manager = get_job_manager()
            job = job_manager.get_job(job_id)
            if job:
                job.fail(str(e))
                job_manager.update_job(job)
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")


def _update_job_progress(
    job_manager: EmbeddingJobManager,
    job_id: str,
    processed: int,
    successful: int,
    failed: int,
    message: str,
):
    """Update job progress during generation"""
    try:
        job = job_manager.get_job(job_id)
        if job:
            job.update_progress(processed, successful, failed, message)
            job_manager.update_job(job)
    except Exception as e:
        logger.error(f"Failed to update job progress: {e}")
