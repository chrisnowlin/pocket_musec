# Database-Backed Presentation Jobs System

This document describes the migration from in-memory job tracking to database-backed job persistence for the presentation generation system.

## Overview

The presentation generation system has been enhanced with robust database persistence to provide:

- **Job Recovery**: Automatic recovery of jobs after server restarts
- **Enhanced Monitoring**: Comprehensive metrics and health monitoring
- **Queue Management**: Priority-based job queuing and management
- **Error Resilience**: Better error handling and retry mechanisms
- **Production Readiness**: Suitable for production deployment

## Key Features

### 1. Database Persistence
- Jobs are stored in SQLite database with comprehensive schema
- Supports job state recovery after system restarts
- Indexes for efficient querying and queue management

### 2. Enhanced Job Model
```python
@dataclass
class PresentationJob:
    # Core fields
    id: str
    lesson_id: str
    user_id: str
    status: JobStatus
    priority: JobPriority
    progress: int
    message: str

    # Timing and configuration
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    timeout_seconds: int
    style: str
    use_llm_polish: bool

    # Result and error handling
    presentation_id: Optional[str]
    slide_count: Optional[int]
    result_data: Optional[Dict[str, Any]]
    retry_count: int
    max_retries: int
    error_code: Optional[str]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]

    # Worker tracking
    worker_id: Optional[str]
    queue_position: Optional[int]
    processing_time_seconds: Optional[float]
```

### 3. Priority System
- **URGENT**: Highest priority, processed first
- **HIGH**: High priority jobs
- **NORMAL**: Default priority
- **LOW**: Lowest priority

### 4. Enhanced Status Tracking
- **PENDING**:等待处理的作业
- **RUNNING**:正在运行的作业
- **COMPLETED**:成功完成的作业
- **FAILED**:失败的作业（可重试）
- **CANCELLED**:被取消的作业
- **TIMEOUT**:超时的作业

### 5. Automatic Recovery
- Orphaned job detection and recovery on startup
- Configurable timeout for orphaned job detection
- Automatic cleanup of old finished jobs

## Migration Steps

### 1. Run Database Migration
```bash
# Using the standalone migration script
cd backend
python migrate_presentation_jobs.py

# Or with custom database path
python migrate_presentation_jobs.py --db-path /path/to/your.db

# Force re-run migration if needed
python migrate_presentation_jobs.py --force
```

### 2. Update Application Startup
The job system now requires initialization on startup:
```python
from backend.services.presentation_jobs import initialize_job_system

# Initialize the job system (recovers orphaned jobs)
job_manager = initialize_job_system()
```

### 3. API Integration
The API now supports enhanced job management:
- Priority-based job creation
- Job retry functionality
- Bulk operations
- Health metrics and monitoring

## New API Endpoints

### Enhanced Job Creation
```http
POST /api/presentations/generate
{
    "lesson_id": "string",
    "style": "default",
    "use_llm_polish": true,
    "timeout_seconds": 30,
    "priority": "normal|high|low|urgent",
    "max_retries": 2
}
```

### Job Management
```http
# Enhanced job listing with filters
GET /api/presentations/jobs?status=pending&priority=high&include_finished=false&limit=20

# Retry a failed job
POST /api/presentations/jobs/{job_id}/retry
{
    "force_retry": false
}

# Bulk cancel operations
POST /api/presentations/jobs/bulk-cancel?reason=cleanup
{
    "job_ids": ["job1", "job2", "job3"]
}

# Cleanup old jobs
DELETE /api/presentations/jobs/cleanup?max_age_hours=24
```

### Monitoring and Health
```http
# Health metrics
GET /api/presentations/jobs/health?hours=24

# Detailed statistics
GET /api/presentations/jobs/statistics?hours=24

# Trigger orphaned job recovery
POST /api/presentations/jobs/system/recovery?timeout_minutes=30
```

## Database Schema

### Table: presentation_jobs
```sql
CREATE TABLE presentation_jobs (
    id TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'normal',
    progress INTEGER DEFAULT 0,
    message TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    timeout_seconds INTEGER DEFAULT 30,
    presentation_id TEXT NULL,
    slide_count INTEGER NULL,
    result_data TEXT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    error_code TEXT NULL,
    error_message TEXT NULL,
    error_details TEXT NULL,
    style TEXT DEFAULT 'default',
    use_llm_polish INTEGER DEFAULT 1,
    worker_id TEXT NULL,
    queue_position INTEGER NULL,
    processing_time_seconds REAL NULL,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
);
```

### Indexes
- `idx_jobs_status`: Fast status-based queries
- `idx_jobs_user_status`: User job filtering
- `idx_jobs_priority_status`: Priority queue management
- `idx_jobs_queue_order`: Optimized pending job ordering
- Additional indexes for lesson and worker tracking

## Configuration

### Environment Variables
```bash
# Database configuration
DATABASE_PATH=./data/pocket_musec.db

# Job system configuration
JOB_TIMEOUT_MINUTES=10
MAX_RETRIES=2
RETRY_DELAYS="0,5,15"
CLEANUP_MAX_AGE_HOURS=24
ORPHANED_JOB_TIMEOUT_MINUTES=30
```

### Application Configuration
```python
# Custom configuration example
job_manager = PresentationJobManager(
    presentation_service=custom_service,
    job_repository=custom_repository
)

# Configure timeouts and retries
job_manager.job_timeout_minutes = 15
job_manager.max_retries = 3
job_manager.retry_delays = [0, 10, 30]
```

## Monitoring Integration

### Health Metrics
```python
metrics = job_manager.get_job_health_metrics()
# Returns:
# {
#     "total": 150,
#     "pending": 5,
#     "running": 2,
#     "completed": 140,
#     "failed": 3,
#     "failure_rate": 2.0,
#     "worker_id": "worker-uuid",
#     "oldest_pending_job_age_minutes": 3.5
# }
```

### Statistics and Analytics
```python
stats = job_repository.get_job_statistics(hours=24)
# Returns comprehensive statistics including:
# - Job counts by status
# - Performance metrics
# - Error rates
# - Priority distribution
# - Queue health indicators
```

## Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-mock

# Run repository tests
python -m pytest backend/tests/test_presentation_jobs_persistent.py -v

# Run API tests
python -m pytest backend/tests/test_presentation_jobs_api.py -v

# Run all job-related tests
python -m pytest backend/tests/ -k presentation_job -v
```

### Test Coverage
- ✅ Repository CRUD operations
- ✅ Job lifecycle management
- ✅ Priority queue ordering
- ✅ Error handling and retry logic
- ✅ Orphaned job recovery
- ✅ API endpoint functionality
- ✅ Authentication and authorization
- ✅ Bulk operations
- ✅ Monitoring and metrics

## Backward Compatibility

The migration maintains backward compatibility:

1. **API Compatibility**: Original job endpoints still work
2. **Client Compatibility**: Existing integrations remain functional
3. **Data Migration**: Seamless upgrade from in-memory to persistent storage

### Legacy Support
```python
# Original job creation still works
job_id = create_presentation_job(
    lesson_id="lesson_123",
    user_id="user_456",
    style="default",
    use_llm_polish=True,
    timeout_seconds=30
)

# Original job status retrieval
status = get_presentation_job_status(job_id)
```

## Performance Considerations

### Database Optimization
- **Indexes**: Optimized for common query patterns
- **Queue Management**: Efficient priority-based ordering
- **Cleanup**: Automatic cleanup of old data
- **Connection Pooling**: Shared connections across operations

### Memory Usage
- **Lazy Loading**: Jobs loaded from database as needed
- **Batch Operations**: Efficient bulk operations
- **Cleanup**: Regular cleanup prevents database bloat

### Scalability
- **Worker Isolation**: Each worker instance has unique ID
- **Concurrent Processing**: Multiple workers can run safely
- **Queue Distribution**: Work can be distributed across workers

## Troubleshooting

### Common Issues

#### 1. Migration Fails
```bash
# Check database permissions
ls -la /path/to/database.db

# Run with verbose logging
python migrate_presentation_jobs.py --verbose
```

#### 2. Jobs Stuck in Running State
```bash
# Trigger manual recovery
curl -X POST "http://localhost:8000/api/presentations/jobs/system/recovery?timeout_minutes=30"
```

#### 3. High Failure Rate
```bash
# Check detailed statistics
curl "http://localhost:8000/api/presentations/jobs/statistics?hours=24"

# Review error logs
tail -f logs/presentation_jobs.log
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('backend.repositories.presentation_job_repository').setLevel(logging.DEBUG)
logging.getLogger('backend.services.presentation_jobs_persistent').setLevel(logging.DEBUG)
```

## Production Deployment

### Monitoring Setup
1. **Health Checks**: Regular calls to `/jobs/health` endpoint
2. **Metrics Collection**: Collect statistics for monitoring systems
3. **Alert Configuration**: Set up alerts for high failure rates
4. **Log Aggregation**: Centralized logging for job events

### Scaling Considerations
1. **Database Sizing**: Ensure adequate storage for job data
2. **Worker Management**: Deploy multiple worker instances
3. **Load Balancing**: Distribute job creation across instances
4. **Backup Strategy**: Regular database backups

### Performance Tuning
1. **Index Optimization**: Monitor and optimize database indexes
2. **Cleanup Frequency**: Adjust cleanup intervals based on usage
3. **Timeout Settings**: Tune timeouts for your environment
4. **Retry Configuration**: Optimize retry strategies

## Future Enhancements

### Planned Features
- **Distributed Queue**: Redis-based queue for multi-node deployments
- **Job Dependencies**: Support for dependent job execution
- **Scheduled Jobs**: Cron-based job scheduling
- **Webhook Notifications**: Job status change notifications
- **Performance Analytics**: Advanced performance insights
- **Queue Prioritization**: Dynamic priority adjustment

### Extensions
- **Custom Job Types**: Support for different job types
- **Job Templates**: Predefined job configurations
- **Bulk Import/Export**: Job data management tools
- **Audit Logging**: Comprehensive audit trail

---

## Support

For questions or issues with the presentation jobs migration:

1. Check the test suite for usage examples
2. Review the API documentation for endpoint details
3. Enable debug logging for troubleshooting
4. Check the troubleshooting section above

The migration provides a solid foundation for scalable, reliable presentation generation job management.