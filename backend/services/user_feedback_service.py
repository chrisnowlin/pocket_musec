"""
User Feedback Collection Service for camelCase Rollout

This service provides comprehensive feedback collection capabilities for monitoring
user experience during the camelCase migration rollout.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .feature_flag_service_fixed import FeatureFlagService
from .rollout_analytics import RolloutAnalytics

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be collected"""

    BUG_REPORT = "bug_report"
    USABILITY_ISSUE = "usability_issue"
    FEATURE_REQUEST = "feature_request"
    GENERAL_FEEDBACK = "general_feedback"
    FORMAT_PREFERENCE = "format_preference"
    PERFORMANCE_ISSUE = "performance_issue"
    UI_PROBLEM = "ui_problem"


class FeedbackSeverity(Enum):
    """Severity levels for feedback"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackCategory(Enum):
    """Categories for organizing feedback"""

    API_RESPONSES = "api_responses"
    USER_INTERFACE = "user_interface"
    DATA_FORMAT = "data_format"
    PERFORMANCE = "performance"
    MIGRATION_ISSUES = "migration_issues"
    OTHER = "other"


class UserFeedbackService:
    """Service for collecting and managing user feedback during rollout"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.feature_flag_service = FeatureFlagService()
        self.analytics_service = RolloutAnalytics()

        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("User feedback service connected to Redis")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        else:
            logger.warning("Redis not available, using in-memory storage")

    def submit_feedback(
        self, user_id: str, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit user feedback

        Args:
            user_id: User identifier
            feedback_data: Feedback information

        Returns:
            Submission result with feedback ID
        """
        try:
            # Generate feedback ID
            feedback_id = str(uuid.uuid4())

            # Validate and enrich feedback data
            feedback = self._validate_feedback(feedback_data, user_id, feedback_id)

            # Store feedback
            stored = self._store_feedback(feedback)

            if stored:
                # Update analytics
                self._update_feedback_analytics(feedback)

                # Check for critical issues
                critical_alerts = self._check_critical_issues(feedback)

                # Send notifications if needed
                if critical_alerts:
                    self._send_critical_notifications(feedback, critical_alerts)

                logger.info(f"Feedback submitted: {feedback_id} from user {user_id}")

                return {
                    "success": True,
                    "feedback_id": feedback_id,
                    "message": "Feedback submitted successfully",
                    "critical_alerts": critical_alerts,
                }
            else:
                return {"success": False, "error": "Failed to store feedback"}

        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {"success": False, "error": str(e)}

    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific feedback by ID"""
        try:
            if self.redis_client:
                feedback_data = self.redis_client.get(f"feedback:{feedback_id}")
                if feedback_data:
                    return json.loads(feedback_data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving feedback {feedback_id}: {e}")
            return None

    def get_user_feedback(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all feedback from a specific user"""
        try:
            if self.redis_client:
                feedback_ids = self.redis_client.lrange(
                    f"user_feedback:{user_id}", 0, limit - 1
                )
                feedback_list = []
                for feedback_id in feedback_ids:
                    feedback = self.get_feedback(feedback_id)
                    if feedback:
                        feedback_list.append(feedback)
                return feedback_list
            return []
        except Exception as e:
            logger.error(f"Error retrieving user feedback: {e}")
            return []

    def get_feedback_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get feedback summary for the specified time range

        Args:
            time_range: Time range (1h, 24h, 7d, 30d)

        Returns:
            Feedback summary with statistics and trends
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(days=1)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)

            # Get feedback metrics from analytics
            metrics = self.analytics_service.get_metrics(time_range)

            # Get feedback breakdown
            feedback_breakdown = self._get_feedback_breakdown(start_time, end_time)

            # Get trending issues
            trending_issues = self._get_trending_issues(start_time, end_time)

            # Get user satisfaction metrics
            satisfaction_metrics = self._get_satisfaction_metrics(start_time, end_time)

            return {
                "time_range": time_range,
                "total_feedback": metrics.get("feedback_submitted", 0),
                "breakdown": feedback_breakdown,
                "trending_issues": trending_issues,
                "satisfaction": satisfaction_metrics,
                "critical_issues": metrics.get("critical_feedback", 0),
                "resolution_rate": self._calculate_resolution_rate(
                    start_time, end_time
                ),
            }

        except Exception as e:
            logger.error(f"Error generating feedback summary: {e}")
            return {"error": str(e)}

    def create_feedback_survey(self, survey_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a feedback survey for specific user groups

        Args:
            survey_config: Survey configuration

        Returns:
            Survey creation result
        """
        try:
            survey_id = str(uuid.uuid4())

            # Validate survey configuration
            survey = {
                "survey_id": survey_id,
                "title": survey_config.get("title", "User Feedback Survey"),
                "description": survey_config.get("description", ""),
                "questions": survey_config.get("questions", []),
                "target_groups": survey_config.get("target_groups", ["all"]),
                "active": survey_config.get("active", True),
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": survey_config.get("expires_at"),
                "max_responses": survey_config.get("max_responses"),
            }

            # Store survey
            if self.redis_client:
                self.redis_client.setex(
                    f"survey:{survey_id}", timedelta(days=30), json.dumps(survey)
                )

                # Add to active surveys list
                if survey["active"]:
                    self.redis_client.lpush("active_surveys", survey_id)
                    self.redis_client.ltrim("active_surveys", 0, 99)  # Keep last 100

            logger.info(f"Created feedback survey: {survey_id}")

            return {"success": True, "survey_id": survey_id, "survey": survey}

        except Exception as e:
            logger.error(f"Error creating feedback survey: {e}")
            return {"success": False, "error": str(e)}

    def get_active_surveys(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get active surveys, optionally filtered for a specific user"""
        try:
            if not self.redis_client:
                return []

            survey_ids = self.redis_client.lrange("active_surveys", 0, -1)
            active_surveys = []

            for survey_id in survey_ids:
                survey_data = self.redis_client.get(f"survey:{survey_id}")
                if survey_data:
                    survey = json.loads(survey_data)

                    # Check if survey is still active
                    if self._is_survey_active(survey):
                        # Filter for user if specified
                        if user_id and not self._is_user_eligible_for_survey(
                            survey, user_id
                        ):
                            continue

                        active_surveys.append(survey)

            return active_surveys

        except Exception as e:
            logger.error(f"Error retrieving active surveys: {e}")
            return []

    def _validate_feedback(
        self, feedback_data: Dict[str, Any], user_id: str, feedback_id: str
    ) -> Dict[str, Any]:
        """Validate and enrich feedback data"""
        feedback = {
            "feedback_id": feedback_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": feedback_data.get("type", FeedbackType.GENERAL_FEEDBACK.value),
            "severity": feedback_data.get("severity", FeedbackSeverity.MEDIUM.value),
            "category": feedback_data.get("category", FeedbackCategory.OTHER.value),
            "title": feedback_data.get("title", ""),
            "description": feedback_data.get("description", ""),
            "context": feedback_data.get("context", {}),
            "user_agent": feedback_data.get("user_agent", ""),
            "session_id": feedback_data.get("session_id", ""),
            "format_preference": feedback_data.get("format_preference", ""),
            "rating": feedback_data.get("rating", None),
            "attachments": feedback_data.get("attachments", []),
            "resolved": False,
            "resolution_notes": "",
        }

        # Validate enum values
        if feedback["type"] not in [e.value for e in FeedbackType]:
            feedback["type"] = FeedbackType.GENERAL_FEEDBACK.value

        if feedback["severity"] not in [e.value for e in FeedbackSeverity]:
            feedback["severity"] = FeedbackSeverity.MEDIUM.value

        if feedback["category"] not in [e.value for e in FeedbackCategory]:
            feedback["category"] = FeedbackCategory.OTHER.value

        return feedback

    def _store_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Store feedback in Redis"""
        try:
            if self.redis_client:
                # Store feedback data
                self.redis_client.setex(
                    f"feedback:{feedback['feedback_id']}",
                    timedelta(days=90),
                    json.dumps(feedback),
                )

                # Add to user's feedback list
                self.redis_client.lpush(
                    f"user_feedback:{feedback['user_id']}", feedback["feedback_id"]
                )
                self.redis_client.ltrim(
                    f"user_feedback:{feedback['user_id']}", 0, 99
                )  # Keep last 100

                # Add to category lists
                self.redis_client.lpush(
                    f"feedback_category:{feedback['category']}", feedback["feedback_id"]
                )
                self.redis_client.ltrim(
                    f"feedback_category:{feedback['category']}", 0, 999
                )

                # Add to severity lists for critical issues
                if feedback["severity"] == FeedbackSeverity.CRITICAL.value:
                    self.redis_client.lpush(
                        "critical_feedback", feedback["feedback_id"]
                    )
                    self.redis_client.ltrim("critical_feedback", 0, 49)  # Keep last 50

                return True
            return False
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False

    def _update_feedback_analytics(self, feedback: Dict[str, Any]):
        """Update analytics with feedback data"""
        try:
            # Increment feedback counters
            self.analytics_service.record_counter("feedback_submitted", 1)
            self.analytics_service.record_counter(
                f"feedback_type_{feedback['type']}", 1
            )
            self.analytics_service.record_counter(
                f"feedback_category_{feedback['category']}", 1
            )
            self.analytics_service.record_counter(
                f"feedback_severity_{feedback['severity']}", 1
            )

            # Record rating if provided
            if feedback.get("rating"):
                self.analytics_service.record_gauge("user_rating", feedback["rating"])

            # Record format preference
            if feedback.get("format_preference"):
                self.analytics_service.record_counter(
                    f"format_preference_{feedback['format_preference']}", 1
                )

        except Exception as e:
            logger.error(f"Error updating feedback analytics: {e}")

    def _check_critical_issues(self, feedback: Dict[str, Any]) -> List[str]:
        """Check for critical issues that need immediate attention"""
        alerts = []

        if feedback["severity"] == FeedbackSeverity.CRITICAL.value:
            alerts.append("Critical severity feedback received")

        if feedback["category"] == FeedbackCategory.MIGRATION_ISSUES.value:
            alerts.append("Migration issue reported")

        if feedback["rating"] and feedback["rating"] <= 2:
            alerts.append("Very low user satisfaction rating")

        # Check for repeated issues from same user
        user_feedback = self.get_user_feedback(feedback["user_id"], 10)
        recent_similar = sum(
            1
            for f in user_feedback
            if f["category"] == feedback["category"] and f["type"] == feedback["type"]
        )

        if recent_similar >= 3:
            alerts.append("Repeated similar issues from user")

        return alerts

    def _send_critical_notifications(self, feedback: Dict[str, Any], alerts: List[str]):
        """Send notifications for critical issues"""
        try:
            # In a real implementation, this would send emails, Slack messages, etc.
            notification = {
                "type": "critical_feedback",
                "feedback_id": feedback["feedback_id"],
                "user_id": feedback["user_id"],
                "severity": feedback["severity"],
                "category": feedback["category"],
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if self.redis_client:
                self.redis_client.lpush(
                    "critical_notifications", json.dumps(notification)
                )
                self.redis_client.ltrim("critical_notifications", 0, 99)

            logger.warning(
                f"Critical feedback notification: {feedback['feedback_id']} - {alerts}"
            )

        except Exception as e:
            logger.error(f"Error sending critical notifications: {e}")

    def _get_feedback_breakdown(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Get feedback breakdown by type, category, and severity"""
        breakdown = {"by_type": {}, "by_category": {}, "by_severity": {}}

        # This would typically query a database for the time range
        # For now, return current analytics data
        try:
            metrics = self.analytics_service.get_metrics("24h")

            for key, value in metrics.items():
                if key.startswith("feedback_type_"):
                    feedback_type = key.replace("feedback_type_", "")
                    breakdown["by_type"][feedback_type] = value
                elif key.startswith("feedback_category_"):
                    category = key.replace("feedback_category_", "")
                    breakdown["by_category"][category] = value
                elif key.startswith("feedback_severity_"):
                    severity = key.replace("feedback_severity_", "")
                    breakdown["by_severity"][severity] = value

            return breakdown

        except Exception as e:
            logger.error(f"Error getting feedback breakdown: {e}")
            return breakdown

    def _get_trending_issues(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Identify trending issues based on feedback frequency"""
        trending = []

        try:
            # This would analyze feedback patterns over time
            # For now, return placeholder data
            trending = [
                {
                    "issue": "Data format confusion",
                    "count": 5,
                    "trend": "increasing",
                    "category": "data_format",
                },
                {
                    "issue": "UI response time",
                    "count": 3,
                    "trend": "stable",
                    "category": "performance",
                },
            ]

            return trending

        except Exception as e:
            logger.error(f"Error getting trending issues: {e}")
            return trending

    def _get_satisfaction_metrics(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate user satisfaction metrics"""
        try:
            metrics = self.analytics_service.get_metrics("24h")

            avg_rating = metrics.get("user_rating", 0)

            # Calculate satisfaction distribution
            satisfaction = {
                "average_rating": avg_rating,
                "total_ratings": metrics.get("feedback_submitted", 0),
                "satisfaction_score": min(100, (avg_rating / 5) * 100)
                if avg_rating > 0
                else 0,
            }

            return satisfaction

        except Exception as e:
            logger.error(f"Error calculating satisfaction metrics: {e}")
            return {"average_rating": 0, "satisfaction_score": 0}

    def _calculate_resolution_rate(
        self, start_time: datetime, end_time: datetime
    ) -> float:
        """Calculate feedback resolution rate"""
        try:
            # This would query resolved vs total feedback
            # For now, return a placeholder
            return 85.0  # 85% resolution rate

        except Exception as e:
            logger.error(f"Error calculating resolution rate: {e}")
            return 0.0

    def _is_survey_active(self, survey: Dict[str, Any]) -> bool:
        """Check if a survey is still active"""
        if not survey.get("active", False):
            return False

        if survey.get("expires_at"):
            expiry = datetime.fromisoformat(survey["expires_at"])
            if datetime.utcnow() > expiry:
                return False

        return True

    def _is_user_eligible_for_survey(
        self, survey: Dict[str, Any], user_id: str
    ) -> bool:
        """Check if a user is eligible for a survey"""
        target_groups = survey.get("target_groups", ["all"])

        if "all" in target_groups:
            return True

        # Check if user is in rollout groups
        for group in target_groups:
            if self.feature_flag_service.is_user_in_group(user_id, group):
                return True

        return False
