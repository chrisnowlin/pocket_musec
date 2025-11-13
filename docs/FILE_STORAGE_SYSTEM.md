# PocketMusec File Storage System

## Overview

The PocketMusec File Storage System is a comprehensive solution for managing uploaded documents with permanent storage, duplicate detection, and organized directory structure. It provides a robust foundation for document ingestion, processing, and retrieval throughout the application.

### Key Features

- **Permanent File Storage**: Files are stored permanently with UUID-based naming to prevent conflicts
- **Duplicate Detection**: SHA256 hash-based detection prevents duplicate uploads
- **Organized Directory Structure**: Date-based organization (YYYY/MM/DD) for efficient management
- **Metadata Tracking**: Comprehensive metadata storage including file status, processing state, and user information
- **Security**: File type validation, size limits, and secure access controls
- **Cleanup Management**: Automated cleanup of old files with configurable retention policies

## Architecture

The file storage system consists of several interconnected components:

```
File Storage System
├── Backend Components
│   ├── FileStorageManager (backend/utils/file_storage.py)
│   ├── FileRepository (backend/repositories/file_repository.py)
│   └── Ingestion API Routes (backend/api/routes/ingestion.py)
├── Frontend Components
│   ├── File Storage Types (frontend/src/types/fileStorage.ts)
│   ├── File Storage Hook (frontend/src/hooks/useFileStorage.ts)
│   ├── Ingestion Service (frontend/src/services/ingestionService.ts)
│   └── UI Components (frontend/src/components/unified/)
└── Database Schema
    └── uploaded_files table (migrations.py)
```

## Configuration Options

### Environment Variables

The file storage system is configured through environment variables in the `.env` file:

```bash
# File Storage Configuration
FILE_STORAGE_ROOT=data/uploads                    # Root directory for file storage
MAX_FILE_SIZE=52428800                         # Maximum file size in bytes (50MB)
ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif
DUPLICATE_DETECTION=true                         # Enable/disable duplicate detection
FILE_RETENTION_DAYS=365                         # Number of days to retain files
FILE_CLEANUP_ENABLED=true                        # Enable/disable automatic cleanup
```

### Configuration Classes

The system uses the unified configuration system in [`backend/config.py`](../backend/config.py):

#### FileStorageConfig

```python
@dataclass
class FileStorageConfig:
    storage_root: str = "data/uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = [".pdf", ".doc", ".docx", ...]
    duplicate_detection: bool = True
    retention_days: int = 365
    cleanup_enabled: bool = True
```

## API Endpoints

### File Upload and Processing

#### POST /ingestion/ingest
Upload and process a document with permanent storage.

**Request:** `multipart/form-data`
- `file` (file): Document file to upload and process
- `advanced_option` (string, optional): Advanced processing options

**Response:**
```json
{
  "success": true,
  "results": {
    "standards_count": 25,
    "objectives_count": 48
  },
  "file_metadata": {
    "id": "file_abc123",
    "file_id": "uuid-filename",
    "original_filename": "NC_Music_Standards.pdf",
    "file_hash": "sha256-hash",
    "file_size": 1048576,
    "mime_type": "application/pdf",
    "document_type": "standards",
    "confidence": 0.95
  }
}
```

### File Management

#### GET /ingestion/files
List uploaded files with optional filtering and pagination.

**Query Parameters:**
- `status` (string, optional): Filter by ingestion status
- `limit` (int, default: 50): Maximum files to return
- `offset` (int, default: 0): Number of files to skip

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "id": "file_abc123",
      "file_id": "uuid-filename",
      "original_filename": "NC_Music_Standards.pdf",
      "ingestion_status": "completed",
      "created_at": "2025-11-12T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 25,
    "count": 25
  }
}
```

#### GET /ingestion/files/{file_id}
Get metadata for a specific file.

**Response:**
```json
{
  "success": true,
  "file": {
    "id": "file_abc123",
    "file_id": "uuid-filename",
    "original_filename": "NC_Music_Standards.pdf",
    "file_hash": "sha256-hash",
    "file_size": 1048576,
    "mime_type": "application/pdf",
    "ingestion_status": "completed",
    "created_at": "2025-11-12T10:00:00Z",
    "metadata": {
      "document_type": "standards",
      "confidence": 0.95
    }
  }
}
```

#### GET /ingestion/files/{file_id}/download
Download a file by its ID.

**Response:** File download with proper headers

#### DELETE /ingestion/files/{file_id}
Delete a file record and optionally the physical file.

**Query Parameters:**
- `delete_physical` (boolean, default: true): Also delete the physical file

**Response:**
```json
{
  "success": true,
  "message": "File NC_Music_Standards.pdf deleted successfully",
  "deleted_physical_file": true
}
```

### Statistics and Maintenance

#### GET /ingestion/files/stats
Get file storage statistics.

**Response:**
```json
{
  "success": true,
  "database_stats": {
    "total_files": 25,
    "total_bytes": 26214400,
    "total_mb": 25.0,
    "completed_files": 20,
    "processing_files": 2,
    "error_files": 1,
    "uploaded_files": 2,
    "files_by_type": {
      "application/pdf": 20,
      "text/plain": 3,
      "image/jpeg": 2
    }
  },
  "storage_stats": {
    "total_files": 25,
    "total_bytes": 26214400,
    "total_bytes_mb": 25.0,
    "file_counts_by_extension": {
      ".pdf": 20,
      ".txt": 3,
      ".jpg": 2
    },
    "storage_root": "/path/to/data/uploads"
  }
}
```

#### POST /ingestion/files/cleanup
Clean up old files and records.

**Query Parameters:**
- `days` (int, optional): Override retention days

**Response:**
```json
{
  "success": true,
  "record_cleanup": {
    "deleted_count": 5,
    "cutoff_date": "2024-11-13T10:00:00Z"
  },
  "physical_cleanup": {
    "enabled": true,
    "deleted_count": 5,
    "freed_bytes": 5242880,
    "cutoff_date": "2024-11-13T10:00:00Z"
  }
}
```

## Database Schema

### uploaded_files Table

The file storage system uses the `uploaded_files` table to track file metadata:

```sql
CREATE TABLE uploaded_files (
    id TEXT PRIMARY KEY,                          -- Unique record ID
    file_id TEXT NOT NULL UNIQUE,                 -- UUID filename
    original_filename TEXT NOT NULL,               -- Original filename from upload
    relative_path TEXT NOT NULL,                   -- Path relative to storage root
    file_hash TEXT NOT NULL,                      -- SHA256 hash for duplicate detection
    file_size INTEGER NOT NULL,                   -- File size in bytes
    mime_type TEXT NOT NULL,                      -- Detected MIME type
    user_id TEXT,                                -- User ID who uploaded the file
    metadata TEXT,                                -- JSON metadata (document type, etc.)
    ingestion_status TEXT DEFAULT 'uploaded',       -- Processing status
    error_message TEXT,                            -- Error message if processing failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Upload timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Last update timestamp
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CHECK (ingestion_status IN ('uploaded', 'processing', 'completed', 'error'))
);
```

### Indexes

Performance is optimized with the following indexes:

```sql
CREATE INDEX idx_uploaded_files_hash ON uploaded_files(file_hash);
CREATE INDEX idx_uploaded_files_status ON uploaded_files(ingestion_status);
CREATE INDEX idx_uploaded_files_user ON uploaded_files(user_id);
CREATE INDEX idx_uploaded_files_created ON uploaded_files(created_at);
CREATE INDEX idx_uploaded_files_file_id ON uploaded_files(file_id);
```

## File Storage Directory Structure

Files are organized in a date-based hierarchy for efficient management:

```
data/uploads/
├── 2025/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── uuid-filename1.pdf
│   │   │   ├── uuid-filename2.jpg
│   │   │   └── uuid-filename3.docx
│   │   └── 16/
│   │       └── uuid-filename4.pdf
│   └── 02/
│       └── 10/
│           └── uuid-filename5.pdf
└── 2024/
    └── 12/
        └── 25/
            └── uuid-filename6.pdf
```

### File Naming Convention

- **UUID-based naming**: Files are renamed with UUIDs to prevent conflicts
- **Extension preservation**: Original file extensions are preserved
- **Example**: `a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf`

## Security Considerations

### File Type Validation

The system validates file types through multiple mechanisms:

1. **Extension Check**: Validates against `ALLOWED_EXTENSIONS` list
2. **MIME Type Detection**: Uses Python's `mimetypes` module
3. **Content Verification**: Optional content-based validation

### File Size Limits

- **Default limit**: 50MB per file
- **Configurable**: Set via `MAX_FILE_SIZE` environment variable
- **Validation**: Checked before upload and processing

### Access Control

- **User isolation**: Files are associated with user IDs
- **Authentication**: All endpoints require valid authentication
- **Authorization**: Users can only access their own files (except admins)

### Path Security

- **Path validation**: All paths are validated to prevent directory traversal
- **Relative paths**: Only relative paths within storage root are allowed
- **UUID naming**: Prevents filename-based attacks

## Best Practices

### For Developers

1. **Use the FileStorageManager**: Always use the provided manager class for file operations
2. **Handle duplicates**: Check for duplicates before processing
3. **Validate files**: Use built-in validation methods
4. **Update status**: Keep file status updated throughout processing
5. **Handle errors gracefully**: Provide meaningful error messages

### For System Administrators

1. **Monitor storage usage**: Use statistics endpoints to track usage
2. **Configure retention**: Set appropriate retention policies
3. **Regular cleanup**: Enable automatic cleanup or run manually
4. **Backup important files**: Implement backup strategies for critical files
5. **Monitor logs**: Check logs for errors and unusual activity

### For Users

1. **Check file requirements**: Ensure files meet size and type requirements
2. **Use descriptive names**: Original filenames are preserved for reference
3. **Monitor processing**: Check file status after upload
4. **Download copies**: Keep local copies of important files
5. **Report issues**: Report any upload or processing problems

## Troubleshooting

### Common Issues

#### Upload Fails with "File Extension Not Allowed"

**Cause**: File extension is not in the allowed list

**Solution**:
1. Check the file extension against the allowed list
2. Convert file to an allowed format if necessary
3. Contact administrator to add new file types

#### Upload Fails with "File Size Exceeds Limit"

**Cause**: File is larger than the configured maximum size

**Solution**:
1. Compress the file if possible
2. Split large documents into smaller parts
3. Request administrator to increase size limit

#### File Processing Stuck at "Processing"

**Cause**: Background processing may have failed or is taking too long

**Solution**:
1. Check backend logs for error messages
2. Try re-uploading the file
3. Contact administrator if issue persists

#### File Download Fails with "File Not Found"

**Cause**: Physical file may have been deleted or path is incorrect

**Solution**:
1. Check if file was recently cleaned up
2. Verify file exists in storage directory
3. Check database record for correct path

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG
```

### Log Locations

- **Backend logs**: `logs/backend.api.app.log`
- **File storage logs**: Included in backend logs
- **Error logs**: `logs/backend.api.app_errors.log`

## Performance Considerations

### Storage Optimization

1. **Use appropriate file formats**: PDF for documents, compressed formats for images
2. **Implement cleanup**: Regular cleanup of old files
3. **Monitor storage usage**: Track usage patterns and plan capacity
4. **Consider external storage**: For large deployments, consider cloud storage

### Database Optimization

1. **Index optimization**: Ensure all indexes are properly maintained
2. **Query optimization**: Use appropriate filters and pagination
3. **Regular maintenance**: Run database maintenance operations
4. **Monitor performance**: Track query performance over time

### Network Optimization

1. **Compression**: Use compression for file transfers
2. **Chunked uploads**: Implement chunked uploads for large files
3. **CDN usage**: Consider CDN for file distribution
4. **Caching**: Implement appropriate caching strategies

## Integration Examples

### Frontend Integration

```typescript
// Using the useFileStorage hook
import { useFileStorage } from '../hooks/useFileStorage';

function FileManager() {
  const {
    files,
    loading,
    error,
    loadFiles,
    downloadFile,
    deleteFile
  } = useFileStorage();

  const handleDownload = async (fileId: string, filename: string) => {
    try {
      await downloadFile(fileId, filename);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    // Component JSX
  );
}
```

### Backend Integration

```python
# Using the FileStorageManager
from backend.utils.file_storage import FileStorageManager
from backend.repositories.file_repository import FileRepository

# Initialize components
file_storage = FileStorageManager()
file_repository = FileRepository()

# Save a file
file_id, relative_path = file_storage.save_file_permanently(
    temp_file_path="/tmp/upload.pdf",
    original_filename="document.pdf"
)

# Create database record
record_id = file_repository.create_file_record(
    original_filename="document.pdf",
    file_id=file_id,
    relative_path=relative_path,
    file_hash="sha256-hash",
    file_size=1024000,
    mime_type="application/pdf",
    user_id="user_123"
)
```

## Migration and Upgrades

### Database Migration

The file storage system includes automatic database migration:

```python
from backend.repositories.migrations import MigrationManager

# Run migrations
migrator = MigrationManager("data/pocket_musec.db")
migrator.migrate()
```

### Version Compatibility

- **Current version**: v7 (file storage system)
- **Backward compatibility**: Maintained for all file operations
- **Upgrade path**: Automatic through migration system

## Future Enhancements

### Planned Features

1. **Cloud Storage Integration**: Support for S3, Azure Blob, Google Cloud Storage
2. **Advanced Deduplication**: Content-based deduplication beyond hash matching
3. **File Versioning**: Track multiple versions of the same file
4. **Batch Operations**: Bulk upload, download, and processing
5. **File Preview**: Generate previews for documents and images

### Performance Improvements

1. **Async Processing**: Full async support for file operations
2. **Caching Layer**: Redis or similar for frequently accessed files
3. **Load Balancing**: Distribute file storage across multiple servers
4. **Compression**: Automatic compression for stored files

---

*This documentation covers the PocketMusec File Storage System as of version 0.3.0. For the latest updates, check the repository documentation.*