# File Storage System Migration Guide

This guide provides comprehensive instructions for migrating existing PocketMusec installations to the new file storage system, including data migration, configuration updates, and validation steps.

## Table of Contents

1. [Overview](#overview)
2. [Migration Prerequisites](#migration-prerequisites)
3. [Migration Steps](#migration-steps)
4. [Data Migration](#data-migration)
5. [Configuration Updates](#configuration-updates)
6. [Validation and Testing](#validation-and-testing)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)
9. [Post-Migration Tasks](#post-migration-tasks)

## Overview

The file storage system migration introduces:

- **Permanent file storage** with UUID-based naming
- **SHA256 duplicate detection**
- **Organized directory structure** (YYYY/MM/DD)
- **Comprehensive metadata tracking**
- **Automated cleanup capabilities**
- **Enhanced security features**

### What Changes

1. **Database Schema**: New `uploaded_files` table to track file metadata
2. **File Organization**: Files moved to date-based directory structure
3. **API Endpoints**: New file management endpoints
4. **Configuration**: Additional environment variables for file storage
5. **Processing Flow**: Updated ingestion process with file tracking

### What Stays the Same

1. **Existing Data**: All existing standards and documents remain accessible
2. **Core Functionality**: Lesson generation and search continue to work
3. **Database Location**: SQLite database stays in the same location
4. **User Interface**: Web interface remains familiar to users

## Migration Prerequisites

### System Requirements

- **Python 3.9+**: Required for new file storage components
- **Disk Space**: Additional space for file reorganization (typically 10% of current data)
- **Database Backup**: Current database must be backed up
- **User Permissions**: Admin access to perform migration

### Pre-Migration Checklist

- [ ] Backup current database (`data/pocket_musec.db`)
- [ ] Backup any files in existing storage locations
- [ ] Note current file storage locations (if any)
- [ ] Test migration in staging environment
- [ ] Schedule migration during maintenance window
- [ ] Notify users of scheduled downtime

### Version Compatibility

- **From**: Any version prior to 0.3.0
- **To**: Version 0.3.0 or later with file storage system
- **Breaking Changes**: None, backward compatible

## Migration Steps

### Step 1: Backup Current System

```bash
# Create backup directory
mkdir -p backups/$(date +%Y-%m-%d)

# Backup database
cp data/pocket_musec.db backups/$(date +%Y-%m-%d)/pocket_musec_before_migration.db

# Backup any existing file storage (if applicable)
if [ -d "data/files" ]; then
    cp -r data/files backups/$(date +%Y-%m-%d)/files_backup
fi

# Verify backups
ls -la backups/$(date +%Y-%m-%d)/
```

### Step 2: Update Application Code

```bash
# Pull latest code
git pull origin main

# Install new dependencies
uv sync

# Verify installation
uv run python -c "from backend.utils.file_storage import FileStorageManager; print('File storage components available')"
```

### Step 3: Update Configuration

Create or update `.env` file with file storage configuration:

```bash
# File Storage Configuration
FILE_STORAGE_ROOT=./data/uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif
DUPLICATE_DETECTION=true
FILE_RETENTION_DAYS=365
FILE_CLEANUP_ENABLED=true
```

### Step 4: Run Database Migration

```bash
# Run automatic migration
uv run python -c "
from backend.repositories.migrations import MigrationManager
migrator = MigrationManager('data/pocket_musec.db')
migrator.migrate()
print('Migration completed successfully')
"

# Verify migration
uv run python -c "
from backend.repositories.migrations import MigrationManager
migrator = MigrationManager('data/pocket_musec.db')
status = migrator.get_migration_status()
print(f'Schema version: {status[\"schema_version\"]}')
print(f'Tables: {status[\"tables\"]}')
"
```

### Step 5: Initialize File Storage

```bash
# Create file storage directories
mkdir -p data/uploads

# Verify directory structure
ls -la data/uploads

# Test file storage manager
uv run python -c "
from backend.utils.file_storage import FileStorageManager
import tempfile

# Test file storage
with tempfile.NamedTemporaryFile() as tmp:
    tmp.write(b'test content')
    tmp.flush()
    
    manager = FileStorageManager()
    file_id, relative_path = manager.save_file_permanently(tmp.name, 'test.txt')
    print(f'File saved: {file_id} at {relative_path}')
    
    # Verify file exists
    assert manager.file_exists(relative_path)
    print('File storage verification successful')
"
```

## Data Migration

### Migrating Existing Files (if applicable)

If you have existing files stored outside the new system:

```python
# migration_script.py
import os
import shutil
from pathlib import Path
from datetime import datetime
from backend.utils.file_storage import FileStorageManager
from backend.repositories.file_repository import FileRepository

def migrate_existing_files(old_storage_path: str, new_storage_manager: FileStorageManager, file_repository: FileRepository):
    """Migrate existing files to new storage system"""
    
    old_path = Path(old_storage_path)
    
    if not old_path.exists():
        print(f"Old storage path {old_path} does not exist, skipping migration")
        return
    
    print(f"Migrating files from {old_path}...")
    
    for file_path in old_path.rglob("*"):
        if file_path.is_file():
            try:
                # Calculate file hash
                file_hash = new_storage_manager.calculate_file_hash(str(file_path))
                
                # Check if already exists
                existing_file = file_repository.get_file_by_hash(file_hash)
                if existing_file:
                    print(f"Skipping duplicate: {file_path.name}")
                    continue
                
                # Save to new storage
                file_id, relative_path = new_storage_manager.save_file_permanently(
                    str(file_path), 
                    file_path.name
                )
                
                # Create database record
                record_id = file_repository.create_file_record(
                    original_filename=file_path.name,
                    file_id=file_id,
                    relative_path=relative_path,
                    file_hash=file_hash,
                    file_size=file_path.stat().st_size,
                    mime_type="application/octet-stream",  # Would need proper detection
                    user_id="migration_user",
                    metadata={
                        "migration_date": datetime.now().isoformat(),
                        "original_path": str(file_path)
                    }
                )
                
                print(f"Migrated: {file_path.name} -> {record_id}")
                
            except Exception as e:
                print(f"Failed to migrate {file_path.name}: {e}")

# Usage
if __name__ == "__main__":
    storage_manager = FileStorageManager()
    repository = FileRepository()
    
    migrate_existing_files(
        old_storage_path="data/old_files",
        new_storage_manager=storage_manager,
        file_repository=repository
    )
```

Run the migration script:

```bash
uv run python migration_script.py
```

### Database Updates

The migration system automatically handles database updates:

1. **Schema Version Tracking**: Automatic version management
2. **Table Creation**: New tables created as needed
3. **Index Creation**: Performance indexes added automatically
4. **Data Preservation**: All existing data preserved

### File Organization Update

Files are automatically reorganized into date-based directories:

```
data/uploads/
├── 2025/          # Year
│   ├── 11/        # Month
│   │   ├── 12/    # Day
│   │   │   ├── file1.pdf
│   │   │   └── file2.docx
```

## Configuration Updates

### Environment Variables

Add to your `.env` file:

```bash
# File Storage Configuration
FILE_STORAGE_ROOT=./data/uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif
DUPLICATE_DETECTION=true
FILE_RETENTION_DAYS=365
FILE_CLEANUP_ENABLED=true
```

### Configuration Classes

The system uses enhanced configuration:

```python
# In backend/config.py
@dataclass
class FileStorageConfig:
    storage_root: str = "data/uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = [...]
    duplicate_detection: bool = True
    retention_days: int = 365
    cleanup_enabled: bool = True
```

### Security Configuration

Update security settings:

```bash
# Optional: Virus scanning (if implemented)
VIRUS_SCANNING_ENABLED=false
VIRUS_SCAN_COMMAND=clamscan

# Optional: File encryption
FILE_ENCRYPTION_ENABLED=false
ENCRYPTION_KEY_PATH=./data/encryption.key
```

## Validation and Testing

### Migration Validation Script

```python
# validate_migration.py
import sys
from backend.repositories.migrations import MigrationManager
from backend.utils.file_storage import FileStorageManager
from backend.repositories.file_repository import FileRepository
from pathlib import Path

def validate_migration():
    """Validate that migration completed successfully"""
    
    print("Validating file storage migration...")
    
    # Check database schema
    migrator = MigrationManager('data/pocket_musec.db')
    schema_version = migrator.get_schema_version()
    
    if schema_version < 7:
        print(f"ERROR: Schema version {schema_version} is too old")
        return False
    
    print(f"✓ Database schema version: {schema_version}")
    
    # Check file storage directory
    storage_root = Path('data/uploads')
    if not storage_root.exists():
        print("ERROR: File storage directory does not exist")
        return False
    
    print(f"✓ File storage directory exists: {storage_root}")
    
    # Test file storage operations
    try:
        import tempfile
        
        manager = FileStorageManager()
        repository = FileRepository()
        
        # Test file save
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"validation test content")
            tmp.flush()
            
            file_id, relative_path = manager.save_file_permanently(tmp.name, "validation_test.txt")
            
            # Test database record
            record_id = repository.create_file_record(
                original_filename="validation_test.txt",
                file_id=file_id,
                relative_path=relative_path,
                file_hash=manager.calculate_file_hash(tmp.name),
                file_size=tmp.tell(),
                mime_type="text/plain"
            )
            
            # Cleanup test record
            repository.delete_file_record(record_id, delete_physical_file=True)
            
        print("✓ File storage operations working correctly")
        
    except Exception as e:
        print(f"ERROR: File storage validation failed: {e}")
        return False
    
    # Check API endpoints
    try:
        from backend.api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test endpoints (would need auth token in real scenario)
        response = client.get("/api/ingestion/document-types")
        if response.status_code != 401:  # Should get auth error, not 404
            print("✓ API endpoints accessible")
        else:
            print("✓ API endpoints properly secured")
            
    except Exception as e:
        print(f"ERROR: API validation failed: {e}")
        return False
    
    print("Migration validation completed successfully!")
    return True

if __name__ == "__main__":
    success = validate_migration()
    sys.exit(0 if success else 1)
```

Run validation:

```bash
uv run python validate_migration.py
```

### Functional Testing

Test key functionality:

```bash
# Test file upload
curl -X POST "http://localhost:8000/api/ingestion/classify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@tests/fixtures/test_document.pdf"

# Test file listing
curl -X GET "http://localhost:8000/api/ingestion/files" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test statistics
curl -X GET "http://localhost:8000/api/ingestion/files/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Rollback Procedures

### Automatic Rollback

If migration fails:

```bash
# Stop application services
pkill -f "pocketmusec"

# Restore database from backup
cp backups/$(date +%Y-%m-%d)/pocket_musec_before_migration.db data/pocket_musec.db

# Restore file storage (if applicable)
if [ -d "backups/$(date +%Y-%m-%d)/files_backup" ]; then
    rm -rf data/files
    cp -r backups/$(date +%Y-%m-%d)/files_backup data/files
fi

# Rollback code (if needed)
git checkout pre_migration_tag

# Restart with previous version
uv run python main.py
```

### Manual Rollback Steps

1. **Stop Services**: Ensure no processes are writing to database
2. **Database Restore**: Replace current database with backup
3. **File Restore**: Restore any migrated files to original locations
4. **Code Rollback**: Revert to previous code version
5. **Configuration**: Restore previous configuration
6. **Validation**: Verify system is working with rolled back version

### Rollback Validation

```bash
# Verify database is accessible
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/pocket_musec.db')
print(f'Database accessible, tables: {conn.execute(\"SELECT name FROM sqlite_master WHERE type=\'table\'\").fetchall()}')
conn.close()
"

# Verify application starts
uv run python main.py --help

# Check web interface
curl -I http://localhost:5173
```

## Troubleshooting

### Common Migration Issues

#### Issue: Database Migration Fails

**Symptoms**:
```
Error: Database migration failed
sqlite3.OperationalError: table "uploaded_files" already exists
```

**Solutions**:
```bash
# Check current schema version
uv run python -c "
from backend.repositories.migrations import MigrationManager
migrator = MigrationManager('data/pocket_musec.db')
print(f'Current version: {migrator.get_schema_version()}')
"

# Force migration status update
uv run python -c "
from backend.repositories.migrations import MigrationManager
migrator = MigrationManager('data/pocket_musec.db')
migrator.set_schema_version(7)  # Set to current version
print('Schema version updated')
"
```

#### Issue: File Permission Errors

**Symptoms**:
```
Error: Permission denied when creating directories
Error: Cannot write to file storage location
```

**Solutions**:
```bash
# Check permissions
ls -la data/
ls -la data/uploads/

# Fix permissions
chmod 755 data/
chmod 755 data/uploads/

# Check ownership
sudo chown -R $USER:$USER data/
```

#### Issue: File Storage Path Problems

**Symptoms**:
```
Error: File storage path not accessible
Error: Cannot save files to storage location
```

**Solutions**:
```bash
# Verify path configuration
uv run python -c "
from backend.config import config
print(f'Storage root: {config.file_storage.storage_root}')
print(f'Path exists: {Path(config.file_storage.storage_root).exists()}')
"

# Create missing directories
mkdir -p data/uploads/2025/11/12

# Update configuration if needed
export FILE_STORAGE_ROOT=$(pwd)/data/uploads
```

#### Issue: API Endpoint Errors

**Symptoms**:
```
Error: 404 Not Found on file endpoints
Error: Authentication failed
```

**Solutions**:
```bash
# Check API routes are registered
curl -X GET "http://localhost:8000/api/docs"  # Should show API documentation

# Verify authentication is working
curl -X GET "http://localhost:8000/api/ingestion/document-types" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Restart API server
pkill -f "uvicorn"
uv run uvicorn backend.api.main:app --reload
```

### Debug Mode Migration

Enable debug logging for migration:

```bash
# Enable debug mode
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# Run migration with debug output
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)

from backend.repositories.migrations import MigrationManager
migrator = MigrationManager('data/pocket_musec.db')
migrator.migrate()
" 2>&1 | tee migration_debug.log
```

### Performance Issues During Migration

For large datasets:

```python
# optimized_migration.py
import time
from backend.repositories.file_repository import FileRepository

def migrate_large_dataset(batch_size=100):
    """Migrate large datasets in batches to avoid memory issues"""
    
    repository = FileRepository()
    
    # Process in batches
    offset = 0
    while True:
        files = repository.list_files_by_status(
            limit=batch_size,
            offset=offset
        )
        
        if not files:
            break
            
        print(f"Processing batch {offset//batch_size + 1}...")
        
        # Process batch
        for file_record in files:
            try:
                # Migration logic for each file
                process_single_file(file_record)
            except Exception as e:
                print(f"Error processing {file_record['id']}: {e}")
        
        offset += batch_size
        time.sleep(0.1)  # Small delay to prevent overload
```

## Post-Migration Tasks

### System Optimization

1. **Database Optimization**:

```bash
# Vacuum database after migration
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/pocket_musec.db')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
print('Database optimization completed')
"
```

2. **Index Rebuilding**:

```bash
# Rebuild indexes for better performance
uv run python -c "
from backend.repositories.file_repository import FileRepository

repository = FileRepository()
stats = repository.get_file_stats()
print(f' indexed {stats[\"total_files\"]} files')
"
```

### Monitoring Setup

Set up monitoring for file storage:

```python
# monitoring_setup.py
from backend.utils.file_storage import FileStorageManager
from backend.repositories.file_repository import FileRepository

def setup_monitoring():
    """Set up monitoring for file storage system"""
    
    storage_manager = FileStorageManager()
    repository = FileRepository()
    
    # Get baseline statistics
    storage_stats = storage_manager.get_storage_stats()
    file_stats = repository.get_file_stats()
    
    print("Baseline Statistics:")
    print(f"Storage: {storage_stats['total_files']} files, {storage_stats['total_bytes_mb']} MB")
    print(f"Database: {file_stats['total_files']} records")
    
    # Set up alerts (would integrate with monitoring system)
    setup_storage_alerts(storage_stats)

def setup_storage_alerts(stats):
    """Configure alerts for storage usage"""
    
    # Alert at 80% storage usage
    if stats.get('total_bytes_mb', 0) > 4096:  # 4GB threshold
        print("WARNING: Storage usage is high")
```

### Documentation Updates

Update internal documentation:

1. **Update operations manual** with new file locations
2. **Update backup procedures** to include file storage
3. **Update monitoring dashboards** with new metrics
4. **Update troubleshooting guides** with common file storage issues

### User Communication

Notify users of changes:

```bash
# Example announcement template
cat > user_announcement.md << EOF
## System Update: Enhanced File Storage

We've upgraded our file storage system to provide:

- Better file organization
- Duplicate file prevention
- Enhanced security features
- Improved performance

### What's New
- Files are now permanently stored with unique identifiers
- Duplicate files are automatically detected
- Download and management improved

### No Action Required
All your existing documents and data remain accessible.
No changes to your workflow are needed.

Questions? Contact support@pocketmusec.org
EOF
```

### Backup Strategy Update

Update backup procedures:

```bash
# updated_backup_script.sh
#!/bin/bash

BACKUP_DIR="backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Backup database
cp data/pocket_musec.db "$BACKUP_DIR/"

# Backup file storage
tar -czf "$BACKUP_DIR/file_storage.tar.gz" data/uploads/

# Verify backup
echo "Backup completed: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
```

---

This migration guide covers all aspects of migrating to the new file storage system. For additional assistance, refer to the [File Storage System Documentation](FILE_STORAGE_SYSTEM.md) or contact the development team.

### Quick Migration Checklist

- [ ] Backup database and files
- [ ] Update application code
- [ ] Configure file storage settings
- [ ] Run database migration
- [ ] Verify file storage operations
- [ ] Test API endpoints
- [ ] Validate migration
- [ ] Update monitoring and backups
- [ ] Notify users of changes

---

*This guide covers migration to the file storage system introduced in PocketMusec v0.3.0*