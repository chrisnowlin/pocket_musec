"""
PocketMuseC Rollout Analytics Service

Provides comprehensive monitoring and analytics for the camelCase migration rollout.
Tracks usage patterns, performance metrics, error rates, and user adoption.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
from collections import defaultdict, deque

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from config.rollout_config import rollout_config
    from services.feature_flag_service import feature_flag_service

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    rollout_config = None
    feature_flag_service = None

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricEvent:
    """Single metric event."""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: MetricType
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metric_type": self.metric_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


class RolloutAnalytics:
    """Analytics service for rollout monitoring."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self._metrics = defaultdict(list)
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(lambda: deque(maxlen=1000))
        self._timers = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
        self._retention_hours = 24 * 7  # Keep data for 7 days
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection for persistent storage."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory analytics only.")
            self.redis_client = None
            return

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for analytics storage")
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Using in-memory analytics only."
            )
            self.redis_client = None

    def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
        format_type: str = "snake_case",
    ) -> None:
        """Track API request metrics."""
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
            "format_type": format_type,
        }

        # Track request count
        self.increment_counter("api_requests_total", tags, user_id)

        # Track response time
        self.record_timer("api_response_time_ms", response_time_ms, tags, user_id)

        # Track error rate
        if status_code >= 400:
            self.increment_counter("api_errors_total", tags, user_id)

        # Track format-specific metrics
        self.increment_counter(f"api_requests_{format_type}", tags, user_id)
        self.record_timer(
            f"api_response_time_{format_type}", response_time_ms, tags, user_id
        )

    def track_format_conversion(
        self,
        conversion_time_ms: float,
        fields_converted: int,
        user_id: Optional[str] = None,
    ) -> None:
        """Track format conversion metrics."""
        tags = {"conversion_type": "snake_to_camel"}

        self.record_timer(
            "format_conversion_time_ms", conversion_time_ms, tags, user_id
        )
        self.record_histogram(
            "fields_converted_per_request", fields_converted, tags, user_id
        )
        self.increment_counter("format_conversions_total", tags, user_id)

    def track_user_adoption(
        self,
        user_id: str,
        format_type: str,
        session_duration_ms: Optional[float] = None,
    ) -> None:
        """Track user adoption metrics."""
        tags = {"format_type": format_type}

        self.increment_counter("user_sessions_total", tags, user_id)
        self.set_gauge("active_users", 1, tags, user_id)

        if session_duration_ms:
            self.record_timer("session_duration_ms", session_duration_ms, tags, user_id)

    def track_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        context: Dict[str, str] = None,
    ) -> None:
        """Track error metrics."""
        tags = {"error_type": error_type}
        if context:
            tags.update(context)

        self.increment_counter("errors_total", tags, user_id)
        self.increment_counter(f"errors_{error_type}", tags, user_id)

    def increment_counter(
        self,
        name: str,
        tags: Dict[str, str] = None,
        user_id: Optional[str] = None,
        value: int = 1,
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value

            # Store in Redis if available
            if self.redis_client:
                try:
                    self.redis_client.incrby(f"counter:{key}", value)
                    self.redis_client.expire(
                        f"counter:{key}", self._retention_hours * 3600
                    )
                except Exception as e:
                    logger.error(f"Failed to store counter in Redis: {e}")

            # Track event
            event = MetricEvent(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type=MetricType.COUNTER,
                user_id=user_id,
            )
            self._store_event(event)

    def set_gauge(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value

            # Store in Redis if available
            if self.redis_client:
                try:
                    self.redis_client.set(f"gauge:{key}", value)
                    self.redis_client.expire(
                        f"gauge:{key}", self._retention_hours * 3600
                    )
                except Exception as e:
                    logger.error(f"Failed to store gauge in Redis: {e}")

            # Track event
            event = MetricEvent(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type=MetricType.GAUGE,
                user_id=user_id,
            )
            self._store_event(event)

    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Record a histogram metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)

            # Store in Redis if available (using Redis streams)
            if self.redis_client:
                try:
                    data = {
                        "value": str(value),
                        "timestamp": str(time.time()),
                        "user_id": user_id or "anonymous",
                    }
                    self.redis_client.xadd(f"histogram:{key}", data)
                    self.redis_client.expire(
                        f"histogram:{key}", self._retention_hours * 3600
                    )
                except Exception as e:
                    logger.error(f"Failed to store histogram in Redis: {e}")

            # Track event
            event = MetricEvent(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type=MetricType.HISTOGRAM,
                user_id=user_id,
            )
            self._store_event(event)

    def record_timer(
        self,
        name: str,
        value_ms: float,
        tags: Dict[str, str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Record a timer metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._timers[key].append(value_ms)

            # Store in Redis if available
            if self.redis_client:
                try:
                    data = {
                        "value_ms": str(value_ms),
                        "timestamp": str(time.time()),
                        "user_id": user_id or "anonymous",
                    }
                    self.redis_client.xadd(f"timer:{key}", data)
                    self.redis_client.expire(
                        f"timer:{key}", self._retention_hours * 3600
                    )
                except Exception as e:
                    logger.error(f"Failed to store timer in Redis: {e}")

            # Track event
            event = MetricEvent(
                name=name,
                value=value_ms,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type=MetricType.TIMER,
                user_id=user_id,
            )
            self._store_event(event)

    def _store_event(self, event: MetricEvent) -> None:
        """Store a metric event."""
        self._metrics[event.name].append(event)

        # Keep only recent events in memory
        if len(self._metrics[event.name]) > 1000:
            self._metrics[event.name] = self._metrics[event.name][-1000:]

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a consistent key from name and tags."""
        if not tags:
            return name

        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of metrics for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        summary = {
            "time_period_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            "api_requests": {
                "total": 0,
                "snake_case": 0,
                "camelcase": 0,
                "error_rate": 0.0,
                "avg_response_time_ms": 0.0,
            },
            "format_conversions": {
                "total": 0,
                "avg_conversion_time_ms": 0.0,
                "avg_fields_converted": 0.0,
            },
            "user_adoption": {
                "total_sessions": 0,
                "snake_case_sessions": 0,
                "camelcase_sessions": 0,
                "camelcase_adoption_rate": 0.0,
            },
            "errors": {"total": 0, "by_type": {}},
        }

        # Process recent events
        for metric_name, events in self._metrics.items():
            recent_events = [e for e in events if e.timestamp >= cutoff_time]

            for event in recent_events:
                if event.name == "api_requests_total":
                    summary["api_requests"]["total"] += event.value
                    format_type = event.tags.get("format_type", "unknown")
                    if format_type == "snake_case":
                        summary["api_requests"]["snake_case"] += event.value
                    elif format_type == "camelcase":
                        summary["api_requests"]["camelcase"] += event.value

                elif event.name == "api_errors_total":
                    summary["api_requests"]["error_rate"] += event.value
                    error_type = event.tags.get("error_type", "unknown")
                    summary["errors"]["by_type"][error_type] = (
                        summary["errors"]["by_type"].get(error_type, 0) + event.value
                    )

                elif event.name == "format_conversions_total":
                    summary["format_conversions"]["total"] += event.value

                elif event.name == "user_sessions_total":
                    summary["user_adoption"]["total_sessions"] += event.value
                    format_type = event.tags.get("format_type", "unknown")
                    if format_type == "snake_case":
                        summary["user_adoption"]["snake_case_sessions"] += event.value
                    elif format_type == "camelcase":
                        summary["user_adoption"]["camelcase_sessions"] += event.value

        # Calculate derived metrics
        total_requests = summary["api_requests"]["total"]
        if total_requests > 0:
            summary["api_requests"]["error_rate"] = (
                summary["api_requests"]["error_rate"] / total_requests
            ) * 100

        total_sessions = summary["user_adoption"]["total_sessions"]
        if total_sessions > 0:
            summary["user_adoption"]["camelcase_adoption_rate"] = (
                summary["user_adoption"]["camelcase_sessions"] / total_sessions
            ) * 100

        # Calculate averages from timers/histograms
        for key, values in self._timers.items():
            if "api_response_time" in key and values:
                summary["api_requests"]["avg_response_time_ms"] = sum(values) / len(
                    values
                )

        for key, values in self._histograms.items():
            if "format_conversion_time" in key and values:
                summary["format_conversions"]["avg_conversion_time_ms"] = sum(
                    values
                ) / len(values)
            elif "fields_converted" in key and values:
                summary["format_conversions"]["avg_fields_converted"] = sum(
                    values
                ) / len(values)

        return summary

    def get_rollout_progress(self) -> Dict[str, Any]:
        """Get current rollout progress and status."""
        if not DEPENDENCIES_AVAILABLE:
            return {"error": "Dependencies not available"}

        try:
            rollout_status = rollout_config.get_rollout_status()
            feature_flags = feature_flag_service.get_flag_stats()

            # Get recent metrics
            metrics_24h = self.get_metrics_summary(24)
            metrics_7d = self.get_metrics_summary(24 * 7)

            progress = {
                "rollout_status": rollout_status,
                "feature_flags": feature_flags,
                "metrics_24h": metrics_24h,
                "metrics_7d": metrics_7d,
                "health_indicators": self._calculate_health_indicators(metrics_24h),
                "recommendations": self._generate_recommendations(
                    metrics_24h, rollout_status
                ),
            }

            return progress

        except Exception as e:
            logger.error(f"Failed to get rollout progress: {e}")
            return {"error": str(e)}

    def _calculate_health_indicators(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Calculate health indicators based on metrics."""
        indicators = {}

        # Error rate health
        error_rate = metrics["api_requests"]["error_rate"]
        if error_rate < 1.0:
            indicators["error_rate"] = "healthy"
        elif error_rate < 5.0:
            indicators["error_rate"] = "warning"
        else:
            indicators["error_rate"] = "critical"

        # Response time health
        response_time = metrics["api_requests"]["avg_response_time_ms"]
        if response_time < 500:
            indicators["response_time"] = "healthy"
        elif response_time < 1000:
            indicators["response_time"] = "warning"
        else:
            indicators["response_time"] = "critical"

        # Adoption rate health
        adoption_rate = metrics["user_adoption"]["camelcase_adoption_rate"]
        if adoption_rate > 50:
            indicators["adoption_rate"] = "healthy"
        elif adoption_rate > 20:
            indicators["adoption_rate"] = "warning"
        else:
            indicators["adoption_rate"] = "critical"

        return indicators

    def _generate_recommendations(
        self, metrics: Dict[str, Any], rollout_status: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on metrics and status."""
        recommendations = []

        error_rate = metrics["api_requests"]["error_rate"]
        adoption_rate = metrics["user_adoption"]["camelcase_adoption_rate"]
        strategy = rollout_status.get("strategy", "disabled")

        if error_rate > 5.0:
            recommendations.append(
                "High error rate detected. Consider pausing rollout."
            )

        if error_rate > 1.0:
            recommendations.append(
                "Error rate elevated. Monitor closely before proceeding."
            )

        if strategy == "percentage" and adoption_rate > 80:
            recommendations.append(
                "High adoption rate. Consider increasing rollout percentage."
            )

        if strategy == "percentage" and adoption_rate < 10:
            recommendations.append(
                "Low adoption rate. Consider user education or rollback."
            )

        if metrics["format_conversions"]["avg_conversion_time_ms"] > 100:
            recommendations.append("Format conversion slow. Consider optimization.")

        if len(recommendations) == 0:
            recommendations.append(
                "All metrics look healthy. Continue current rollout strategy."
            )

        return recommendations

    def export_metrics(self, format: str = "json", hours: int = 24) -> str:
        """Export metrics in specified format."""
        metrics = self.get_metrics_summary(hours)

        if format.lower() == "json":
            return json.dumps(metrics, indent=2)
        elif format.lower() == "csv":
            return self._metrics_to_csv(metrics)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _metrics_to_csv(self, metrics: Dict[str, Any]) -> str:
        """Convert metrics to CSV format."""
        lines = ["metric,category,value"]

        for category, data in metrics.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        lines.append(f"{key},{category},{value}")

        return "\n".join(lines)

    def clear_old_metrics(self, hours: int = 24 * 7) -> None:
        """Clear metrics older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            for metric_name in list(self._metrics.keys()):
                self._metrics[metric_name] = [
                    e for e in self._metrics[metric_name] if e.timestamp >= cutoff_time
                ]

                # Remove empty metric lists
                if not self._metrics[metric_name]:
                    del self._metrics[metric_name]

        logger.info(f"Cleared metrics older than {hours} hours")


# Global analytics instance
rollout_analytics = RolloutAnalytics()


def track_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    user_id: Optional[str] = None,
    format_type: str = "snake_case",
) -> None:
    """Convenience function to track API requests."""
    rollout_analytics.track_api_request(
        endpoint, method, status_code, response_time_ms, user_id, format_type
    )


def get_rollout_progress() -> Dict[str, Any]:
    """Convenience function to get rollout progress."""
    return rollout_analytics.get_rollout_progress()
