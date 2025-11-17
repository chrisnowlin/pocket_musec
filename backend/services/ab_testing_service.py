"""
PocketMuseC A/B Testing Service

Provides A/B testing infrastructure for comparing snake_case vs camelCase API formats.
Tracks user behavior, performance metrics, and preferences to inform rollout decisions.
"""

import os
import json
import logging
import uuid
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import random

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from config.rollout_config import rollout_config
    from services.feature_flag_service import feature_flag_service
    from services.rollout_analytics import rollout_analytics

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    rollout_config = None
    feature_flag_service = None
    rollout_analytics = None

logger = logging.getLogger(__name__)


class TestGroup(Enum):
    """A/B test groups."""

    CONTROL = "control"  # snake_case
    VARIANT = "variant"  # camelCase
    EXCLUDED = "excluded"


class TestStatus(Enum):
    """Test status types."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ABTest:
    """A/B test definition."""

    test_id: str
    name: str
    description: str
    status: TestStatus
    traffic_split: Dict[str, float]  # group -> percentage
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_audience: Dict[str, Any] = None
    success_metrics: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.target_audience is None:
            self.target_audience = {}
        if self.success_metrics is None:
            self.success_metrics = []


@dataclass
class TestAssignment:
    """User assignment to A/B test group."""

    test_id: str
    user_id: str
    group: TestGroup
    assigned_at: datetime
    context: Dict[str, Any] = None


class ABTestingService:
    """Service for managing A/B tests and user assignments."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self._tests = {}
        self._assignments = {}  # user_id -> test_id -> group
        self._lock = threading.RLock()
        self._init_redis()
        self._load_default_test()

    def _init_redis(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory A/B testing only.")
            self.redis_client = None
            return

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for A/B testing storage")
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Using in-memory A/B testing only."
            )
            self.redis_client = None

    def _load_default_test(self):
        """Load default camelCase format A/B test."""
        default_test = ABTest(
            test_id="camelcase_format_test",
            name="camelCase vs snake_case API Format",
            description="Compare user experience and performance between camelCase and snake_case API responses",
            status=TestStatus.DRAFT,
            traffic_split={
                TestGroup.CONTROL.value: 50.0,  # snake_case
                TestGroup.VARIANT.value: 50.0,  # camelCase
            },
            target_audience={
                "user_types": ["teacher", "admin"],
                "exclude_integrations": True,
            },
            success_metrics=[
                "api_response_time",
                "error_rate",
                "user_satisfaction",
                "integration_compatibility",
            ],
        )

        with self._lock:
            self._tests[default_test.test_id] = default_test

        # Store in Redis if available
        if self.redis_client:
            self._store_test_in_redis(default_test)

    def _store_test_in_redis(self, test: ABTest):
        """Store test configuration in Redis."""
        if not self.redis_client:
            return

        try:
            test_data = {
                **asdict(test),
                "status": test.status.value,
                "created_at": test.created_at.isoformat() if test.created_at else None,
                "updated_at": test.updated_at.isoformat() if test.updated_at else None,
                "start_time": test.start_time.isoformat() if test.start_time else None,
                "end_time": test.end_time.isoformat() if test.end_time else None,
            }
            self.redis_client.set(f"ab_test:{test.test_id}", json.dumps(test_data))
        except Exception as e:
            logger.error(f"Failed to store test in Redis: {e}")

    def create_test(
        self,
        name: str,
        description: str,
        traffic_split: Dict[str, float],
        target_audience: Dict[str, Any] = None,
        success_metrics: List[str] = None,
    ) -> str:
        """Create a new A/B test."""
        test_id = str(uuid.uuid4())

        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            status=TestStatus.DRAFT,
            traffic_split=traffic_split,
            target_audience=target_audience or {},
            success_metrics=success_metrics or [],
        )

        with self._lock:
            self._tests[test_id] = test

        self._store_test_in_redis(test)
        logger.info(f"Created A/B test: {test_id}")
        return test_id

    def start_test(self, test_id: str) -> bool:
        """Start an A/B test."""
        with self._lock:
            test = self._tests.get(test_id)
            if not test:
                return False

            test.status = TestStatus.RUNNING
            test.start_time = datetime.utcnow()
            test.updated_at = datetime.utcnow()

        self._store_test_in_redis(test)
        logger.info(f"Started A/B test: {test_id}")
        return True

    def pause_test(self, test_id: str) -> bool:
        """Pause an A/B test."""
        with self._lock:
            test = self._tests.get(test_id)
            if not test:
                return False

            test.status = TestStatus.PAUSED
            test.updated_at = datetime.utcnow()

        self._store_test_in_redis(test)
        logger.info(f"Paused A/B test: {test_id}")
        return True

    def complete_test(self, test_id: str) -> bool:
        """Complete an A/B test."""
        with self._lock:
            test = self._tests.get(test_id)
            if not test:
                return False

            test.status = TestStatus.COMPLETED
            test.end_time = datetime.utcnow()
            test.updated_at = datetime.utcnow()

        self._store_test_in_redis(test)
        logger.info(f"Completed A/B test: {test_id}")
        return True

    def assign_user_to_group(
        self, test_id: str, user_id: str, user_context: Dict[str, Any] = None
    ) -> Optional[TestGroup]:
        """Assign a user to a test group."""
        with self._lock:
            test = self._tests.get(test_id)
            if not test or test.status != TestStatus.RUNNING:
                return None

            # Check if user is already assigned
            if test_id in self._assignments.get(user_id, {}):
                return self._assignments[user_id][test_id]

            # Check if user should be excluded
            if self._should_exclude_user(test, user_id, user_context):
                group = TestGroup.EXCLUDED
            else:
                # Assign to control or variant based on traffic split
                group = self._assign_group_by_traffic(test, user_id)

            # Store assignment
            if user_id not in self._assignments:
                self._assignments[user_id] = {}
            self._assignments[user_id][test_id] = group

            # Store in Redis
            if self.redis_client:
                self._store_assignment_in_redis(test_id, user_id, group, user_context)

            # Track assignment in analytics
            if rollout_analytics:
                rollout_analytics.increment_counter(
                    "ab_test_assignments",
                    {"test_id": test_id, "group": group.value},
                    user_id,
                )

            logger.info(
                f"Assigned user {user_id} to group {group.value} in test {test_id}"
            )
            return group

    def _should_exclude_user(
        self, test: ABTest, user_id: str, user_context: Dict[str, Any] = None
    ) -> bool:
        """Check if user should be excluded from test."""
        target_audience = test.target_audience

        # Exclude integration users
        if target_audience.get("exclude_integrations", False):
            if user_context and user_context.get("user_type") == "integration":
                return True
            if user_id.startswith("integration_") or user_id.startswith("api_"):
                return True

        # Check user type inclusion
        allowed_types = target_audience.get("user_types", [])
        if allowed_types and user_context:
            user_type = user_context.get("user_type")
            if user_type not in allowed_types:
                return True

        return False

    def _assign_group_by_traffic(self, test: ABTest, user_id: str) -> TestGroup:
        """Assign user to group based on traffic split."""
        # Use consistent hashing for stable assignment
        hash_input = f"{test.test_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        hash_percentage = (hash_value % 100) + 1  # 1-100

        cumulative = 0
        for group, percentage in test.traffic_split.items():
            cumulative += percentage
            if hash_percentage <= cumulative:
                return TestGroup(group)

        # Fallback to control
        return TestGroup.CONTROL

    def _store_assignment_in_redis(
        self,
        test_id: str,
        user_id: str,
        group: TestGroup,
        user_context: Dict[str, Any] = None,
    ):
        """Store user assignment in Redis."""
        if not self.redis_client:
            return

        try:
            assignment = TestAssignment(
                test_id=test_id,
                user_id=user_id,
                group=group,
                assigned_at=datetime.utcnow(),
                context=user_context or {},
            )

            assignment_data = {
                **asdict(assignment),
                "group": group.value,
                "assigned_at": assignment.assigned_at.isoformat(),
            }

            self.redis_client.set(
                f"ab_assignment:{test_id}:{user_id}",
                json.dumps(assignment_data),
                ex=7 * 24 * 3600,  # 7 days expiry
            )
        except Exception as e:
            logger.error(f"Failed to store assignment in Redis: {e}")

    def get_user_group(self, test_id: str, user_id: str) -> Optional[TestGroup]:
        """Get the group a user is assigned to."""
        with self._lock:
            return self._assignments.get(user_id, {}).get(test_id)

    def get_test_results(self, test_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get A/B test results and analysis."""
        with self._lock:
            test = self._tests.get(test_id)
            if not test:
                return {"error": "Test not found"}

        # Get metrics from analytics service
        if rollout_analytics:
            metrics = rollout_analytics.get_metrics_summary(hours)
        else:
            metrics = {}

        # Analyze results by group
        results = {
            "test_id": test_id,
            "test_name": test.name,
            "status": test.status.value,
            "start_time": test.start_time.isoformat() if test.start_time else None,
            "end_time": test.end_time.isoformat() if test.end_time else None,
            "traffic_split": test.traffic_split,
            "analysis_period_hours": hours,
            "group_metrics": {},
            "statistical_significance": {},
            "recommendations": [],
        }

        # Calculate group-specific metrics
        for group in [TestGroup.CONTROL, TestGroup.VARIANT]:
            group_results = self._analyze_group_metrics(group.value, metrics)
            results["group_metrics"][group.value] = group_results

        # Calculate statistical significance
        results["statistical_significance"] = self._calculate_statistical_significance(
            results["group_metrics"]
        )

        # Generate recommendations
        results["recommendations"] = self._generate_test_recommendations(
            test, results["group_metrics"], results["statistical_significance"]
        )

        return results

    def _analyze_group_metrics(
        self, group: str, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze metrics for a specific group."""
        group_metrics = {
            "api_requests": 0,
            "avg_response_time_ms": 0,
            "error_rate": 0,
            "user_satisfaction": 0,
            "conversion_events": 0,
        }

        # Extract group-specific metrics from the analytics data
        # This would be enhanced with actual group filtering in the analytics service
        if "api_requests" in metrics:
            group_metrics["api_requests"] = metrics["api_requests"].get("total", 0)
            group_metrics["avg_response_time_ms"] = metrics["api_requests"].get(
                "avg_response_time_ms", 0
            )
            group_metrics["error_rate"] = metrics["api_requests"].get("error_rate", 0)

        return group_metrics

    def _calculate_statistical_significance(
        self, group_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate statistical significance for test results."""
        # Simplified statistical analysis
        control_metrics = group_metrics.get("control", {})
        variant_metrics = group_metrics.get("variant", {})

        significance = {
            "sample_size_sufficient": False,
            "confidence_level": 0.95,
            "p_value": None,
            "statistically_significant": False,
            "effect_size": None,
        }

        # Check sample size
        control_size = control_metrics.get("api_requests", 0)
        variant_size = variant_metrics.get("api_requests", 0)
        total_size = control_size + variant_size

        if total_size >= 1000:  # Minimum sample size
            significance["sample_size_sufficient"] = True

            # Simplified t-test calculation (would use proper statistical library)
            control_error_rate = control_metrics.get("error_rate", 0)
            variant_error_rate = variant_metrics.get("error_rate", 0)

            if control_error_rate > 0 and variant_error_rate > 0:
                # Calculate effect size
                significance["effect_size"] = (
                    abs(variant_error_rate - control_error_rate) / control_error_rate
                )

                # Simplified significance test
                if significance["effect_size"] > 0.1:  # 10% difference threshold
                    significance["statistically_significant"] = True
                    significance["p_value"] = 0.05  # Simplified

        return significance

    def _generate_test_recommendations(
        self, test: ABTest, group_metrics: Dict[str, Any], significance: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        if not significance["sample_size_sufficient"]:
            recommendations.append("Insufficient sample size. Continue running test.")
            return recommendations

        if significance["statistically_significant"]:
            control_metrics = group_metrics.get("control", {})
            variant_metrics = group_metrics.get("variant", {})

            # Compare error rates
            control_error = control_metrics.get("error_rate", 0)
            variant_error = variant_metrics.get("error_rate", 0)

            if variant_error < control_error:
                recommendations.append(
                    "camelCase format shows lower error rates. Consider full rollout."
                )
            elif variant_error > control_error * 1.1:
                recommendations.append(
                    "camelCase format shows higher error rates. Investigate issues before proceeding."
                )

            # Compare response times
            control_time = control_metrics.get("avg_response_time_ms", 0)
            variant_time = variant_metrics.get("avg_response_time_ms", 0)

            if variant_time < control_time * 0.9:
                recommendations.append(
                    "camelCase format shows better performance. Favor for rollout."
                )
            elif variant_time > control_time * 1.1:
                recommendations.append(
                    "camelCase format shows performance degradation. Optimize before rollout."
                )
        else:
            recommendations.append(
                "No statistically significant difference detected. Consider extending test or evaluating other factors."
            )

        return recommendations

    def get_all_tests(self) -> List[ABTest]:
        """Get all A/B tests."""
        return list(self._tests.values())

    def get_active_tests(self) -> List[ABTest]:
        """Get currently running A/B tests."""
        return [
            test for test in self._tests.values() if test.status == TestStatus.RUNNING
        ]

    def should_use_camelcase(
        self, user_id: str, user_context: Dict[str, Any] = None
    ) -> bool:
        """
        Determine if a user should receive camelCase format based on A/B testing.
        This is the main method to be called by API endpoints.
        """
        # Check if A/B testing is enabled via feature flags
        if feature_flag_service and not feature_flag_service.is_enabled(
            "AB_TESTING_ENABLED"
        ):
            # Fall back to regular rollout configuration
            if DEPENDENCIES_AVAILABLE:
                from services.feature_flag_service import is_camelcase_enabled

                return is_camelcase_enabled(user_id)
            return False

        # Get active tests
        active_tests = self.get_active_tests()

        for test in active_tests:
            group = self.assign_user_to_group(test.test_id, user_id, user_context)
            if group == TestGroup.VARIANT:
                return True
            elif group == TestGroup.CONTROL:
                return False

        # No active tests, fall back to regular rollout
        if DEPENDENCIES_AVAILABLE:
            from services.feature_flag_service import is_camelcase_enabled

            return is_camelcase_enabled(user_id)

        return False


# Global A/B testing service instance
ab_testing_service = ABTestingService()


def should_use_camelcase(user_id: str, user_context: Dict[str, Any] = None) -> bool:
    """Convenience function to determine if user should receive camelCase format."""
    return ab_testing_service.should_use_camelcase(user_id, user_context)


def get_test_results(test_id: str, hours: int = 24) -> Dict[str, Any]:
    """Convenience function to get A/B test results."""
    return ab_testing_service.get_test_results(test_id, hours)
