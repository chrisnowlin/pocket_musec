# Database Consolidation Guide

## Overview

PocketMusec has been consolidated to use a single database file for all data storage. This simplifies management, backup, and deployment while maintaining all existing functionality.

## New Database Location

- **Single Database**: `data/pocket_musec.db`
- **Old Location**: `data/standards/standards.db` (deprecated)

## What Changed

### Configuration Files
- `.env` and `.env.example` now default to `data/pocket_musec.db`
- `backend/config.py` updated to use the new default path
- All documentation updated to reflect the single database

### Code Updates
- All repository classes now use centralized configuration
- API server updated to use consolidated database
- Migration scripts updated for new location

### Migration Script
A comprehensive consolidation script is available at `scripts/consolidate_database.py`:

```bash
# Run consolidation with backup
python scripts/consolidate_database.py --backup

# Verify existing consolidation
python scripts/consolidate_database.py --verify-only

# Custom source/target paths
python scripts/consolidate_database.py --source-db /old/path --target-db /new/path
```

## Database Schema

The consolidated database contains all tables in a single SQLite file:

### Core Tables
- `standards` - Music education standards
- `objectives` - Learning objectives linked to standards
- `users` - User accounts and authentication
- `sessions` - Lesson generation sessions
- `lessons` - Generated and saved lessons
- `images` - Uploaded and processed images
- `citations` - Source citations for lessons

### Extended Tables
- `unpacking_sections` - Standards unpacking content
- `teaching_strategies` - Pedagogical strategies
- `assessment_guidance` - Assessment recommendations
- `alignment_relationships` - Cross-standard relationships
- `progression_mappings` - Skill progression across grades
- `glossary_entries` - Terminology definitions
- `faq_entries` - Frequently asked questions
- `resource_entries` - Additional educational resources

## Benefits

1. **Simplified Management**: Single file to backup, migrate, and manage
2. **Consistent Configuration**: One `DATABASE_PATH` setting for all components
3. **Easier Deployment**: Fewer files to track and deploy
4. **Better Performance**: Reduced connection overhead
5. **Simplified Debugging**: Single source of truth for all data

## Migration Instructions

### For New Installations
No action needed - the system will automatically create `data/pocket_musec.db` on first run.

### For Existing Installations

1. **Automatic Migration** (recommended):
   ```bash
   python scripts/consolidate_database.py --backup
   ```

2. **Manual Steps**:
   ```bash
   # 1. Update your .env file
   DATABASE_PATH=data/pocket_musec.db
   
   # 2. Run migration
   python scripts/consolidate_database.py
   
   # 3. Test your application
   make dev
   
   # 4. Remove old database after verification
   rm data/standards/standards.db
   ```

### Verification

After consolidation, verify the migration:

```bash
# Check database schema version
python -c "from backend.repositories.migrations import MigrationManager; print('Version:', MigrationManager('data/pocket_musec.db').get_schema_version())"

# Check table structure
python -c "from backend.repositories.migrations import MigrationManager; status = MigrationManager('data/pocket_musec.db').get_migration_status(); print('Tables:', status['tables'])"
```

## Troubleshooting

### Database Not Found
If you get "database not found" errors:
1. Ensure `DATABASE_PATH` in `.env` points to `data/pocket_musec.db`
2. Run database initialization: `python scripts/consolidate_database.py`

### Migration Issues
If migration fails:
1. Check file permissions on the data directory
2. Ensure no other processes are using the database
3. Run with `--backup` flag to create safety copy

### Performance Issues
For better performance:
1. Place the database on fast storage (SSD)
2. Consider SQLite `PRAGMA` optimizations
3. Regularly run `VACUUM` to compact the database

## Backups

### Simple Backup
```bash
cp data/pocket_musec.db data/pocket_musec.db.backup.$(date +%Y%m%d)
```

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
cp data/pocket_musec.db "$BACKUP_DIR/pocket_musec.db.backup.$(date +%Y%m%d_%H%M%S)"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "pocket_musec.db.backup.*" -mtime +7 -delete
```

## Environment-Specific Paths

### Development
```bash
DATABASE_PATH=data/pocket_musec.db
```

### Production
```bash
DATABASE_PATH=/var/lib/pocketmusec/pocket_musec.db
```

### Testing
```bash
DATABASE_PATH=/tmp/test_pocket_musec.db
```

## Migration Scripts

The consolidation script provides several options:

```bash
# Help and options
python scripts/consolidate_database.py --help

# Verify existing consolidation
python scripts/consolidate_database.py --verify-only

# Custom paths
python scripts/consolidate_database.py --source-db old.db --target-db new.db

# Dry run (no changes)
python scripts/consolidate_database.py --dry-run
```

## Notes for Developers

- All existing API endpoints work unchanged
- Repository classes automatically use the consolidated database
- Test files should continue to use temporary databases for isolation
- No code changes required for existing functionality

## History

- **2025-11-12**: Database consolidation completed
- **Before**: Multiple database files and hardcoded paths
- **After**: Single `data/pocket_musec.db` with centralized configuration