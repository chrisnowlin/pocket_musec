# User Feedback Collection System

## Overview

The User Feedback Collection System provides comprehensive feedback collection capabilities for monitoring user experience during the camelCase migration rollout. This system enables real-time feedback collection, analysis, and response to ensure a smooth transition.

## Components

### 1. UserFeedbackService

**Location**: `backend/services/user_feedback_service.py`

The core service responsible for:
- Collecting and validating user feedback
- Storing feedback with Redis persistence
- Analyzing feedback patterns and trends
- Managing feedback surveys
- Sending critical issue notifications

#### Key Features

- **Multiple Feedback Types**: Bug reports, usability issues, feature requests, format preferences
- **Severity Levels**: Low, Medium, High, Critical with automatic escalation
- **Categorized Organization**: API responses, UI, data format, performance, migration issues
- **Real-time Analytics**: Integration with rollout analytics for immediate insights
- **Survey Management**: Create targeted surveys for specific user groups

### 2. Feedback API Routes

**Location**: `backend/api/routes/feedback.py`

RESTful API endpoints for:
- Submitting feedback (`POST /feedback/submit`)
- Retrieving feedback (`GET /feedback/{feedback_id}`)
- User feedback history (`GET /feedback/user/{user_id}`)
- Feedback summaries (`GET /feedback/summary/{time_range}`)
- Survey management (`POST /feedback/surveys`, `GET /feedback/surveys/active`)
- Metadata endpoints for types, severities, categories

### 3. Test Suite

**Location**: `backend/tests/test_user_feedback_service.py`

Comprehensive test coverage including:
- Feedback submission and validation
- Critical issue detection
- Analytics integration
- Survey creation and management
- Redis fallback handling

## Feedback Types

### Type Categories

1. **Bug Report** - Technical issues and errors
2. **Usability Issue** - Difficulty using interface features
3. **Feature Request** - Suggestions for new functionality
4. **General Feedback** - General comments and suggestions
5. **Format Preference** - User preferences for snake_case vs camelCase
6. **Performance Issue** - Speed and performance problems
7. **UI Problem** - User interface specific issues

### Severity Levels

1. **Low** - Minor issues or suggestions
2. **Medium** - Moderate issues affecting usability
3. **High** - Significant issues impacting functionality
4. **Critical** - Issues requiring immediate attention

### Feedback Categories

1. **API Responses** - Issues with API response formats
2. **User Interface** - UI/UX related problems
3. **Data Format** - Data structure and format issues
4. **Performance** - Performance and speed concerns
5. **Migration Issues** - Problems related to camelCase migration
6. **Other** - Issues not covered above

## Usage Examples

### Submitting Feedback

```python
from backend.services.user_feedback_service import UserFeedbackService

service = UserFeedbackService()

feedback_data = {
    "title": "Confusing field names in API response",
    "description": "The mixed use of snake_case and camelCase is confusing",
    "type": "format_preference",
    "severity": "medium",
    "category": "api_responses",
    "format_preference": "camelCase",
    "rating": 3,
    "context": {
        "endpoint": "/api/lessons",
        "user_agent": "Mozilla/5.0...",
        "session_id": "sess_123"
    }
}

result = service.submit_feedback("user_123", feedback_data)
```

### Creating a Survey

```python
survey_config = {
    "title": "CamelCase Migration Feedback",
    "description": "Help us improve the migration experience",
    "questions": [
        {
            "type": "rating",
            "question": "How satisfied are you with the new camelCase format?",
            "scale": "1-5"
        },
        {
            "type": "choice",
            "question": "Which format do you prefer?",
            "options": ["snake_case", "camelCase", "no preference"]
        }
    ],
    "target_groups": ["early_adopters", "internal_users"],
    "active": True,
    "expires_at": "2025-12-31T23:59:59Z"
}

result = service.create_feedback_survey(survey_config)
```

### Getting Feedback Summary

```python
summary = service.get_feedback_summary("24h")

print(f"Total feedback: {summary['total_feedback']}")
print(f"Average rating: {summary['satisfaction']['average_rating']}")
print(f"Critical issues: {summary['critical_issues']}")
print(f"Resolution rate: {summary['resolution_rate']}%")
```

## Critical Issue Detection

The system automatically detects critical issues that require immediate attention:

### Triggers

1. **Critical Severity** - Any feedback marked as critical
2. **Migration Issues** - Problems specifically related to the camelCase migration
3. **Low Ratings** - User ratings of 2 or below
4. **Repeated Issues** - 3+ similar issues from the same user

### Notifications

When critical issues are detected:
- Added to critical notifications queue
- Logged for monitoring systems
- Can trigger email/Slack alerts (configurable)

## Analytics Integration

The feedback system integrates with the rollout analytics service:

### Tracked Metrics

- `feedback_submitted` - Total feedback count
- `feedback_type_{type}` - Count by feedback type
- `feedback_category_{category}` - Count by category
- `feedback_severity_{severity}` - Count by severity level
- `user_rating` - Average user rating
- `format_preference_{format}` - Format preference counts
- `critical_feedback` - Critical issue count

### Health Indicators

- User satisfaction scores
- Issue resolution rates
- Trending problem detection
- Adoption metrics

## Survey System

### Survey Types

1. **General Satisfaction** - Overall user experience
2. **Format Preference** - snake_case vs camelCase preferences
3. **Feature-Specific** - Feedback on particular features
4. **Migration Experience** - Specific to camelCase rollout

### Targeting

- **All Users** - General surveys
- **User Groups** - Early adopters, internal users, etc.
- **Format Groups** - Users receiving camelCase vs snake_case
- **Time-Based** - Users active in specific time periods

## Configuration

### Redis Configuration

```python
# Default Redis connection
service = UserFeedbackService(redis_url="redis://localhost:6379")

# Custom Redis configuration
service = UserFeedbackService(redis_url="redis://user:pass@host:port/db")
```

### Feature Flag Integration

The system integrates with feature flags for:
- Enabling/disabling feedback collection
- Targeting specific user groups
- Controlling survey visibility

## Data Retention

### Feedback Storage

- **Individual Feedback**: 90 days
- **User History**: Last 100 feedback items per user
- **Critical Issues**: Last 50 critical feedback items
- **Surveys**: 30 days (configurable)

### Analytics Data

- **Counters**: Aggregated metrics stored indefinitely
- **Time Series**: 24-hour rolling window
- **Health Indicators**: Real-time calculations

## API Response Formats

### Feedback Submission Response

```json
{
    "success": true,
    "feedback_id": "fb_123456789",
    "message": "Feedback submitted successfully",
    "critical_alerts": ["Critical severity feedback received"]
}
```

### Feedback Summary Response

```json
{
    "time_range": "24h",
    "total_feedback": 25,
    "breakdown": {
        "by_type": {"general_feedback": 15, "bug_report": 5},
        "by_category": {"api_responses": 10, "user_interface": 8},
        "by_severity": {"medium": 12, "high": 8}
    },
    "trending_issues": [
        {
            "issue": "Data format confusion",
            "count": 5,
            "trend": "increasing",
            "category": "data_format"
        }
    ],
    "satisfaction": {
        "average_rating": 4.2,
        "total_ratings": 20,
        "satisfaction_score": 84.0
    },
    "critical_issues": 2,
    "resolution_rate": 85.0
}
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Feedback Volume** - Sudden increases may indicate issues
2. **Critical Issues** - Should be addressed immediately
3. **User Satisfaction** - Track rating trends over time
4. **Format Preferences** - Monitor adoption of camelCase
5. **Resolution Rate** - Ensure issues are being addressed

### Alert Thresholds

- **Critical Issues**: Any critical feedback triggers alert
- **Low Satisfaction**: Average rating below 3.0
- **High Volume**: 50% increase in feedback volume
- **Resolution Rate**: Below 70% resolution rate

## Best Practices

### For Users

1. **Provide Context** - Include relevant session and user agent information
2. **Be Specific** - Detailed descriptions help with troubleshooting
3. **Use Appropriate Severity** - Reserve critical for urgent issues
4. **Include Ratings** - Helps track overall satisfaction

### For Developers

1. **Monitor Critical Issues** - Check critical notifications regularly
2. **Analyze Trends** - Use feedback summaries to identify patterns
3. **Respond Promptly** - Acknowledge and address user feedback
4. **Update Resolution Status** - Mark issues as resolved when fixed

### For Product Managers

1. **Review Summaries** - Regular feedback summary reviews
2. **Track Satisfaction** - Monitor user satisfaction trends
3. **Plan Surveys** - Use surveys for targeted feedback collection
4. **Inform Roadmap** - Use feedback to prioritize improvements

## Integration with Rollout System

The feedback system is designed to work seamlessly with the camelCase rollout:

1. **Feature Flag Control** - Enable feedback collection for rollout groups
2. **A/B Testing Integration** - Compare feedback between format groups
3. **Analytics Correlation** - Correlate feedback with rollout metrics
4. **Gradual Deployment** - Scale feedback collection with rollout percentage

## Troubleshooting

### Common Issues

1. **Redis Connection Failed** - Falls back to in-memory storage
2. **Missing Analytics Service** - Continues with basic functionality
3. **Invalid Feedback Data** - Automatically validates and corrects
4. **Survey Expiration** - Automatically removes expired surveys

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('backend.services.user_feedback_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Machine Learning Analysis** - Automatic categorization and sentiment analysis
2. **Integration with External Systems** - Jira, GitHub Issues, Slack
3. **Advanced Reporting** - Custom dashboards and reports
4. **Feedback Loop Automation** - Automatic responses and follow-ups
5. **Multi-language Support** - Feedback collection in multiple languages

### Scalability Improvements

1. **Database Persistence** - Long-term storage beyond Redis
2. **Distributed Processing** - Handle high-volume feedback scenarios
3. **Real-time Streaming** - Live feedback updates and notifications
4. **Advanced Analytics** - Predictive analytics and trend forecasting