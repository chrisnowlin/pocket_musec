"""
Test suite for User Feedback Service

Tests the feedback collection, storage, and analysis functionality
for the camelCase rollout.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from backend.services.user_feedback_service import (
    UserFeedbackService,
    FeedbackType,
    FeedbackSeverity,
    FeedbackCategory,
)


class TestUserFeedbackService:
    """Test cases for UserFeedbackService"""

    @pytest.fixture
    def feedback_service(self):
        """Create a feedback service instance for testing"""
        with patch("backend.services.user_feedback_service.redis"):
            service = UserFeedbackService()
            service.redis_client = Mock()
            return service

    @pytest.fixture
    def sample_feedback_data(self):
        """Sample feedback data for testing"""
        return {
            "title": "Test Feedback",
            "description": "This is a test feedback submission",
            "type": FeedbackType.GENERAL_FEEDBACK.value,
            "severity": FeedbackSeverity.MEDIUM.value,
            "category": FeedbackCategory.API_RESPONSES.value,
            "context": {"page": "lessons", "action": "create"},
            "user_agent": "TestAgent/1.0",
            "session_id": "test_session_123",
            "format_preference": "camelCase",
            "rating": 4,
        }

    def test_submit_feedback_success(self, feedback_service, sample_feedback_data):
        """Test successful feedback submission"""
        # Mock Redis operations
        feedback_service.redis_client.setex.return_value = True
        feedback_service.redis_client.lpush.return_value = True
        feedback_service.redis_client.ltrim.return_value = True

        # Mock analytics service
        feedback_service.analytics_service = Mock()
        feedback_service.analytics_service.record_counter = Mock()
        feedback_service.analytics_service.record_gauge = Mock()

        result = feedback_service.submit_feedback("test_user", sample_feedback_data)

        assert result["success"] is True
        assert "feedback_id" in result
        assert result["message"] == "Feedback submitted successfully"

        # Verify Redis storage calls
        feedback_service.redis_client.setex.assert_called()
        feedback_service.redis_client.lpush.assert_called()

        # Verify analytics calls
        feedback_service.analytics_service.record_counter.assert_called()
        feedback_service.analytics_service.record_gauge.assert_called()

    def test_submit_feedback_critical_issue(
        self, feedback_service, sample_feedback_data
    ):
        """Test feedback submission with critical severity"""
        # Make it critical
        sample_feedback_data["severity"] = FeedbackSeverity.CRITICAL.value

        # Mock Redis operations
        feedback_service.redis_client.setex.return_value = True
        feedback_service.redis_client.lpush.return_value = True
        feedback_service.redis_client.ltrim.return_value = True

        # Mock analytics service
        feedback_service.analytics_service = Mock()
        feedback_service.analytics_service.record_counter = Mock()

        result = feedback_service.submit_feedback("test_user", sample_feedback_data)

        assert result["success"] is True
        assert len(result["critical_alerts"]) > 0
        assert "Critical severity feedback received" in result["critical_alerts"]

    def test_submit_feedback_low_rating(self, feedback_service, sample_feedback_data):
        """Test feedback submission with low rating"""
        # Make rating very low
        sample_feedback_data["rating"] = 1

        # Mock Redis operations
        feedback_service.redis_client.setex.return_value = True
        feedback_service.redis_client.lpush.return_value = True
        feedback_service.redis_client.ltrim.return_value = True

        # Mock analytics service
        feedback_service.analytics_service = Mock()
        feedback_service.analytics_service.record_counter = Mock()
        feedback_service.analytics_service.record_gauge = Mock()

        result = feedback_service.submit_feedback("test_user", sample_feedback_data)

        assert result["success"] is True
        assert len(result["critical_alerts"]) > 0
        assert "Very low user satisfaction rating" in result["critical_alerts"]

    def test_get_feedback_success(self, feedback_service):
        """Test retrieving feedback by ID"""
        feedback_id = "test_feedback_123"
        sample_feedback = {
            "feedback_id": feedback_id,
            "user_id": "test_user",
            "title": "Test Feedback",
            "description": "Test description",
        }

        feedback_service.redis_client.get.return_value = json.dumps(sample_feedback)

        result = feedback_service.get_feedback(feedback_id)

        assert result is not None
        assert result["feedback_id"] == feedback_id
        assert result["user_id"] == "test_user"

        feedback_service.redis_client.get.assert_called_once_with(
            f"feedback:{feedback_id}"
        )

    def test_get_feedback_not_found(self, feedback_service):
        """Test retrieving non-existent feedback"""
        feedback_service.redis_client.get.return_value = None

        result = feedback_service.get_feedback("nonexistent_id")

        assert result is None

    def test_get_user_feedback(self, feedback_service):
        """Test retrieving all feedback from a user"""
        user_id = "test_user"
        feedback_ids = ["fb1", "fb2", "fb3"]

        # Mock Redis list operations
        feedback_service.redis_client.lrange.return_value = feedback_ids

        # Mock individual feedback retrieval
        sample_feedbacks = [
            {"feedback_id": "fb1", "user_id": user_id},
            {"feedback_id": "fb2", "user_id": user_id},
            {"feedback_id": "fb3", "user_id": user_id},
        ]

        def mock_get_feedback(key):
            feedback_id = key.split(":")[1]
            for feedback in sample_feedbacks:
                if feedback["feedback_id"] == feedback_id:
                    return json.dumps(feedback)
            return None

        feedback_service.redis_client.get.side_effect = mock_get_feedback

        result = feedback_service.get_user_feedback(user_id)

        assert len(result) == 3
        assert all(fb["user_id"] == user_id for fb in result)

    def test_get_feedback_summary(self, feedback_service):
        """Test generating feedback summary"""
        # Mock analytics service
        mock_metrics = {
            "feedback_submitted": 25,
            "feedback_type_bug_report": 5,
            "feedback_category_api_responses": 10,
            "feedback_severity_high": 3,
            "user_rating": 4.2,
        }

        feedback_service.analytics_service = Mock()
        feedback_service.analytics_service.get_metrics.return_value = mock_metrics

        result = feedback_service.get_feedback_summary("24h")

        assert result["time_range"] == "24h"
        assert result["total_feedback"] == 25
        assert "breakdown" in result
        assert "trending_issues" in result
        assert "satisfaction" in result
        assert result["satisfaction"]["average_rating"] == 4.2

    def test_create_feedback_survey(self, feedback_service):
        """Test creating a feedback survey"""
        survey_config = {
            "title": "Test Survey",
            "description": "Test survey description",
            "questions": [
                {"type": "rating", "question": "How satisfied are you?"},
                {"type": "text", "question": "Any additional feedback?"},
            ],
            "target_groups": ["early_adopters"],
            "active": True,
        }

        feedback_service.redis_client.setex.return_value = True
        feedback_service.redis_client.lpush.return_value = True
        feedback_service.redis_client.ltrim.return_value = True

        result = feedback_service.create_feedback_survey(survey_config)

        assert result["success"] is True
        assert "survey_id" in result
        assert result["survey"]["title"] == "Test Survey"
        assert len(result["survey"]["questions"]) == 2

        # Verify Redis storage
        feedback_service.redis_client.setex.assert_called()
        feedback_service.redis_client.lpush.assert_called_with(
            "active_surveys", result["survey_id"]
        )

    def test_get_active_surveys(self, feedback_service):
        """Test retrieving active surveys"""
        survey_ids = ["survey1", "survey2"]

        # Mock active surveys list
        feedback_service.redis_client.lrange.return_value = survey_ids

        # Mock individual survey retrieval
        sample_surveys = [
            {
                "survey_id": "survey1",
                "title": "Survey 1",
                "active": True,
                "target_groups": ["all"],
            },
            {
                "survey_id": "survey2",
                "title": "Survey 2",
                "active": True,
                "target_groups": ["early_adopters"],
            },
        ]

        def mock_get_survey(key):
            survey_id = key.split(":")[1]
            for survey in sample_surveys:
                if survey["survey_id"] == survey_id:
                    return json.dumps(survey)
            return None

        feedback_service.redis_client.get.side_effect = mock_get_survey

        result = feedback_service.get_active_surveys()

        assert len(result) == 2
        assert all(survey["active"] for survey in result)

    def test_get_active_surveys_for_user(self, feedback_service):
        """Test retrieving active surveys filtered for specific user"""
        survey_ids = ["survey1", "survey2"]

        # Mock active surveys list
        feedback_service.redis_client.lrange.return_value = survey_ids

        # Mock surveys with different target groups
        sample_surveys = [
            {
                "survey_id": "survey1",
                "title": "Survey 1",
                "active": True,
                "target_groups": ["all"],
            },
            {
                "survey_id": "survey2",
                "title": "Survey 2",
                "active": True,
                "target_groups": ["early_adopters"],
            },
        ]

        def mock_get_survey(key):
            survey_id = key.split(":")[1]
            for survey in sample_surveys:
                if survey["survey_id"] == survey_id:
                    return json.dumps(survey)
            return None

        feedback_service.redis_client.get.side_effect = mock_get_survey

        # Mock feature flag service for user group checking
        feedback_service.feature_flag_service = Mock()
        feedback_service.feature_flag_service.is_user_in_group.return_value = False

        result = feedback_service.get_active_surveys("test_user")

        # Should only return survey1 (targeted to "all")
        assert len(result) == 1
        assert result[0]["survey_id"] == "survey1"

    def test_validate_feedback_data(self, feedback_service):
        """Test feedback data validation and enrichment"""
        feedback_data = {
            "title": "Test",
            "description": "Test description",
            "invalid_type": "invalid_value",
            "invalid_severity": "invalid_value",
        }

        feedback = feedback_service._validate_feedback(
            feedback_data, "test_user", "fb123"
        )

        assert feedback["feedback_id"] == "fb123"
        assert feedback["user_id"] == "test_user"
        assert "timestamp" in feedback
        # Should default to valid enum values
        assert feedback["type"] == FeedbackType.GENERAL_FEEDBACK.value
        assert feedback["severity"] == FeedbackSeverity.MEDIUM.value
        assert feedback["category"] == FeedbackCategory.OTHER.value

    def test_check_critical_issues_migration(self, feedback_service):
        """Test critical issue detection for migration problems"""
        feedback_data = {
            "category": FeedbackCategory.MIGRATION_ISSUES.value,
            "severity": FeedbackSeverity.HIGH.value,
            "rating": 2,
        }

        alerts = feedback_service._check_critical_issues(feedback_data)

        assert "Migration issue reported" in alerts
        assert "Very low user satisfaction rating" in alerts

    def test_redis_fallback_handling(self, sample_feedback_data):
        """Test service behavior when Redis is not available"""
        with patch("backend.services.user_feedback_service.redis", None):
            service = UserFeedbackService()

            result = service.submit_feedback("test_user", sample_feedback_data)

            # Should fail gracefully when Redis is not available
            assert result["success"] is False
            assert "Failed to store feedback" in result["error"]

    def test_feedback_analytics_update(self, feedback_service, sample_feedback_data):
        """Test that feedback submission updates analytics correctly"""
        # Mock Redis operations
        feedback_service.redis_client.setex.return_value = True
        feedback_service.redis_client.lpush.return_value = True
        feedback_service.redis_client.ltrim.return_value = True

        # Mock analytics service
        mock_analytics = Mock()
        feedback_service.analytics_service = mock_analytics

        feedback_service.submit_feedback("test_user", sample_feedback_data)

        # Verify analytics calls
        mock_analytics.record_counter.assert_any_call("feedback_submitted", 1)
        mock_analytics.record_counter.assert_any_call(
            "feedback_type_general_feedback", 1
        )
        mock_analytics.record_counter.assert_any_call(
            "feedback_category_api_responses", 1
        )
        mock_analytics.record_counter.assert_any_call("feedback_severity_medium", 1)
        mock_analytics.record_gauge.assert_any_call("user_rating", 4)
        mock_analytics.record_counter.assert_any_call("format_preference_camelCase", 1)


if __name__ == "__main__":
    pytest.main([__file__])
