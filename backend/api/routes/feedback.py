"""
Feedback API Routes for camelCase Rollout

API endpoints for collecting and managing user feedback during the rollout.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..services.user_feedback_service import (
    UserFeedbackService,
    FeedbackType,
    FeedbackSeverity,
    FeedbackCategory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Pydantic models for request/response
class FeedbackRequest(BaseModel):
    title: str = Field(..., description="Brief title of the feedback")
    description: str = Field(..., description="Detailed description of the feedback")
    type: str = Field(
        default=FeedbackType.GENERAL_FEEDBACK.value, description="Type of feedback"
    )
    severity: str = Field(
        default=FeedbackSeverity.MEDIUM.value, description="Severity level"
    )
    category: str = Field(
        default=FeedbackCategory.OTHER.value, description="Feedback category"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    user_agent: str = Field(default="", description="User agent string")
    session_id: str = Field(default="", description="Session identifier")
    format_preference: str = Field(
        default="", description="User's format preference (snake_case/camelCase)"
    )
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")
    attachments: List[str] = Field(
        default_factory=list, description="List of attachment URLs"
    )


class FeedbackResponse(BaseModel):
    success: bool
    feedback_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    critical_alerts: List[str] = Field(default_factory=list)


class SurveyRequest(BaseModel):
    title: str = Field(..., description="Survey title")
    description: str = Field(default="", description="Survey description")
    questions: List[Dict[str, Any]] = Field(..., description="Survey questions")
    target_groups: List[str] = Field(default=["all"], description="Target user groups")
    active: bool = Field(default=True, description="Whether survey is active")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    max_responses: Optional[int] = Field(None, description="Maximum responses")


class SurveyResponse(BaseModel):
    success: bool
    survey_id: Optional[str] = None
    survey: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FeedbackSummaryResponse(BaseModel):
    time_range: str
    total_feedback: int
    breakdown: Dict[str, Any]
    trending_issues: List[Dict[str, Any]]
    satisfaction: Dict[str, Any]
    critical_issues: int
    resolution_rate: float


# Dependency to get feedback service
def get_feedback_service():
    return UserFeedbackService()


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous",  # In real app, get from auth
    service: UserFeedbackService = Depends(get_feedback_service),
):
    """
    Submit user feedback
    """
    try:
        feedback_data = feedback.dict()
        result = service.submit_feedback(user_id, feedback_data)

        if result["success"]:
            # Add background task to process feedback
            background_tasks.add_task(
                process_feedback_background,
                result["feedback_id"],
                user_id,
                feedback_data,
            )
            return FeedbackResponse(**result)
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to submit feedback")
            )

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: str, service: UserFeedbackService = Depends(get_feedback_service)
):
    """
    Retrieve specific feedback by ID
    """
    try:
        feedback = service.get_feedback(feedback_id)
        if feedback:
            return JSONResponse(content=feedback)
        else:
            raise HTTPException(status_code=404, detail="Feedback not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_feedback(
    user_id: str,
    limit: int = 50,
    service: UserFeedbackService = Depends(get_feedback_service),
):
    """
    Get all feedback from a specific user
    """
    try:
        feedback_list = service.get_user_feedback(user_id, limit)
        return JSONResponse(
            content={
                "user_id": user_id,
                "feedback_count": len(feedback_list),
                "feedback": feedback_list,
            }
        )

    except Exception as e:
        logger.error(f"Error retrieving user feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{time_range}", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(
    time_range: str = "24h",
    service: UserFeedbackService = Depends(get_feedback_service),
):
    """
    Get feedback summary for the specified time range
    """
    try:
        if time_range not in ["1h", "24h", "7d", "30d"]:
            raise HTTPException(
                status_code=400, detail="Invalid time range. Use: 1h, 24h, 7d, 30d"
            )

        summary = service.get_feedback_summary(time_range)
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])

        return FeedbackSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feedback summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surveys", response_model=SurveyResponse)
async def create_feedback_survey(
    survey: SurveyRequest, service: UserFeedbackService = Depends(get_feedback_service)
):
    """
    Create a feedback survey for specific user groups
    """
    try:
        survey_config = survey.dict()
        result = service.create_feedback_survey(survey_config)

        if result["success"]:
            return SurveyResponse(**result)
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to create survey")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating survey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/surveys/active")
async def get_active_surveys(
    user_id: Optional[str] = None,
    service: UserFeedbackService = Depends(get_feedback_service),
):
    """
    Get active surveys, optionally filtered for a specific user
    """
    try:
        surveys = service.get_active_surveys(user_id)
        return JSONResponse(content={"survey_count": len(surveys), "surveys": surveys})

    except Exception as e:
        logger.error(f"Error retrieving active surveys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_feedback_types():
    """
    Get available feedback types
    """
    return JSONResponse(
        content={
            "types": [e.value for e in FeedbackType],
            "descriptions": {
                FeedbackType.BUG_REPORT.value: "Report a bug or technical issue",
                FeedbackType.USABILITY_ISSUE.value: "Report difficulty using the interface",
                FeedbackType.FEATURE_REQUEST.value: "Request a new feature",
                FeedbackType.GENERAL_FEEDBACK.value: "General comments or suggestions",
                FeedbackType.FORMAT_PREFERENCE.value: "Preference for data format (snake_case/camelCase)",
                FeedbackType.PERFORMANCE_ISSUE.value: "Report performance problems",
                FeedbackType.UI_PROBLEM.value: "Report user interface issues",
            },
        }
    )


@router.get("/severities")
async def get_feedback_severities():
    """
    Get available severity levels
    """
    return JSONResponse(
        content={
            "severities": [e.value for e in FeedbackSeverity],
            "descriptions": {
                FeedbackSeverity.LOW.value: "Minor issue or suggestion",
                FeedbackSeverity.MEDIUM.value: "Moderate issue affecting usability",
                FeedbackSeverity.HIGH.value: "Significant issue impacting functionality",
                FeedbackSeverity.CRITICAL.value: "Critical issue requiring immediate attention",
            },
        }
    )


@router.get("/categories")
async def get_feedback_categories():
    """
    Get available feedback categories
    """
    return JSONResponse(
        content={
            "categories": [e.value for e in FeedbackCategory],
            "descriptions": {
                FeedbackCategory.API_RESPONSES.value: "Issues with API response formats",
                FeedbackCategory.USER_INTERFACE.value: "UI/UX related issues",
                FeedbackCategory.DATA_FORMAT.value: "Data format and structure issues",
                FeedbackCategory.PERFORMANCE.value: "Performance and speed issues",
                FeedbackCategory.MIGRATION_ISSUES.value: "Problems related to camelCase migration",
                FeedbackCategory.OTHER.value: "Other issues not covered above",
            },
        }
    )


async def process_feedback_background(
    feedback_id: str, user_id: str, feedback_data: Dict[str, Any]
):
    """
    Background task to process submitted feedback
    """
    try:
        # Log feedback for monitoring
        logger.info(f"Processing feedback {feedback_id} from user {user_id}")

        # Could add additional processing here:
        # - Send email notifications
        # - Update external monitoring systems
        # - Trigger automated responses
        # - Update user satisfaction scores

        # For now, just log the processing
        logger.debug(f"Feedback data: {feedback_data}")

    except Exception as e:
        logger.error(f"Error processing feedback in background: {e}")
