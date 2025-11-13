"""File repository for PocketMusec

Handles database operations for uploaded files including metadata,
status tracking, and duplicate detection.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import logging

from .database import DatabaseManager
from ..utils.file_storage import FileStorageManager
from ..config import config

logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for managing uploaded file records in the database"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize file repository
        
        Args:
            db_manager: Database manager instance. If None, creates new instance.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.file_storage = FileStorageManager()
    
    def create_file_record(
        self,
        original_filename: str,
        file_id: str,
        relative_path: str, 
        file_hash: str,
        file_size: int,
        mime_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new file record in the database
        
        Args:
            original_filename: Original filename from upload
            file_id: Unique UUID filename
            relative_path: Path relative to storage root
            file_hash: SHA256 hash of the file
            file_size: File size in bytes
            mime_type: MIME type of the file
            user_id: Optional user ID who uploaded the file
            metadata: Additional metadata as JSON string
            
        Returns:
            The database record ID
        """
        import json
        
        record_id = str(uuid.uuid4())
        
        try:
            with self.db_manager.get_connection() as conn:
                try:
                    # Start explicit transaction with immediate locking
                    conn.execute("BEGIN IMMEDIATE")
                    
                    logger.debug(f"Creating file record for {original_filename} with ID {record_id}")
                    
                    conn.execute("""
                        INSERT INTO uploaded_files (
                            id, file_id, original_filename, relative_path,
                            file_hash, file_size, mime_type, user_id,
                            metadata, ingestion_status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record_id, file_id, original_filename, relative_path,
                        file_hash, file_size, mime_type, user_id,
                        json.dumps(metadata) if metadata else None,
                        "uploaded", datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                    
                    # Commit the transaction
                    conn.commit()
                    logger.info(f"Created file record: {record_id} for {original_filename}")
                    
                except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                    # Rollback on any error
                    conn.rollback()
                    logger.error(f"Failed to create file record for {original_filename}, rolled back: {e}")
                    raise
                    
            return record_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error creating file record (possible duplicate): {e}")
            raise ValueError(f"File record already exists or violates constraints: {str(e)}")
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error creating file record: {e}")
            raise RuntimeError(f"Database operation failed: {str(e)}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error creating file record: {e}")
            raise RuntimeError(f"Database error: {str(e)}")
        except (json.JSONEncodeError, TypeError) as e:
            logger.error(f"Metadata encoding error: {e}")
            raise ValueError(f"Invalid metadata format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating file record: {e}")
            raise RuntimeError(f"Failed to create file record: {str(e)}")
    
    def get_file_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by database record ID
        
        Args:
            record_id: Database record ID
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM uploaded_files WHERE id = ?
                """, (record_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error getting file by ID {record_id}: {e}")
            return None
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error getting file by ID {record_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file by ID {record_id}: {e}")
            return None
    
    def get_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by file hash (for duplicate detection)
        
        Args:
            file_hash: SHA256 hash of the file
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM uploaded_files WHERE file_hash = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (file_hash,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error getting file by hash {file_hash}: {e}")
            return None
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error getting file by hash {file_hash}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file by hash {file_hash}: {e}")
            return None
    
    def update_ingestion_status(
        self, 
        record_id: str, 
        status: str, 
        error_message: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the ingestion status of a file
        
        Args:
            record_id: Database record ID
            status: New status (uploaded, processing, completed, error)
            error_message: Optional error message if status is error
            metadata_update: Optional metadata to merge with existing metadata
            
        Returns:
            True if update was successful, False otherwise
        """
        import json
        
        try:
            with self.db_manager.get_connection() as conn:
                try:
                    # Start explicit transaction with immediate locking
                    conn.execute("BEGIN IMMEDIATE")
                    
                    logger.debug(f"Updating ingestion status for {record_id} to {status}")
                    
                    # Get current metadata if we need to update it
                    current_metadata = None
                    if metadata_update:
                        cursor = conn.execute("""
                            SELECT metadata FROM uploaded_files WHERE id = ?
                        """, (record_id,))
                        row = cursor.fetchone()
                        if row and row[0]:
                            current_metadata = json.loads(row[0])
                        else:
                            current_metadata = {}
                        current_metadata.update(metadata_update)
                    
                    if metadata_update:
                        conn.execute("""
                            UPDATE uploaded_files
                            SET ingestion_status = ?, error_message = ?,
                                metadata = ?, updated_at = ?
                            WHERE id = ?
                        """, (
                            status, error_message,
                            json.dumps(current_metadata),
                            datetime.now().isoformat(), record_id
                        ))
                    else:
                        conn.execute("""
                            UPDATE uploaded_files
                            SET ingestion_status = ?, error_message = ?, updated_at = ?
                            WHERE id = ?
                        """, (
                            status, error_message,
                            datetime.now().isoformat(), record_id
                        ))
                    
                    # Commit the transaction
                    conn.commit()
                    logger.info(f"Updated ingestion status for {record_id} to {status}")
                    
                except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                    # Rollback on any error
                    conn.rollback()
                    logger.error(f"Failed to update ingestion status for {record_id}, rolled back: {e}")
                    return False
                    
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error updating ingestion status for {record_id}: {e}")
            return False
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error updating ingestion status for {record_id}: {e}")
            return False
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Metadata encoding error updating ingestion status for {record_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating ingestion status for {record_id}: {e}")
            return False
    
    def list_files_by_status(
        self, 
        status: Optional[str] = None, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List files by status with pagination
        
        Args:
            status: Filter by ingestion status. If None, returns all files.
            limit: Maximum number of files to return
            offset: Number of files to skip
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            with self.db_manager.get_connection() as conn:
                if status:
                    cursor = conn.execute("""
                        SELECT * FROM uploaded_files
                        WHERE ingestion_status = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (status, limit, offset))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM uploaded_files
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error listing files by status {status}: {e}")
            return []
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error listing files by status {status}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files by status {status}: {e}")
            return []
    
    def get_files_by_user(
        self, 
        user_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get files uploaded by a specific user
        
        Args:
            user_id: User ID to filter by
            limit: Maximum number of files to return
            offset: Number of files to skip
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM uploaded_files
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error getting files for user {user_id}: {e}")
            return []
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error getting files for user {user_id}: {e}")
            return []
        except ValueError as e:
            logger.error(f"Invalid parameter getting files for user {user_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting files for user {user_id}: {e}")
            return []
    
    def delete_file_record(self, record_id: str, delete_physical_file: bool = True) -> bool:
        """Delete a file record from database and optionally the physical file
        
        Args:
            record_id: Database record ID to delete
            delete_physical_file: Whether to also delete the physical file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                try:
                    # Start explicit transaction with immediate locking
                    conn.execute("BEGIN IMMEDIATE")
                    
                    logger.info(f"AUDIT: Attempting to delete file record {record_id}")
                    
                    # Get file info before deletion
                    cursor = conn.execute("""
                        SELECT relative_path, original_filename FROM uploaded_files WHERE id = ?
                    """, (record_id,))
                    
                    row = cursor.fetchone()
                    relative_path = row[0] if row else None
                    original_filename = row[1] if row else "unknown"
                    
                    if not row:
                        logger.warning(f"File record {record_id} not found for deletion")
                        return False
                    
                    logger.info(f"AUDIT: Deleting record for file {original_filename} (ID: {record_id})")
                    
                    # Delete database record
                    cursor = conn.execute("""
                        DELETE FROM uploaded_files WHERE id = ?
                    """, (record_id,))
                    
                    deleted_count = cursor.rowcount
                    if deleted_count == 0:
                        logger.warning(f"No records deleted for file {record_id}")
                    
                    # Commit the transaction
                    conn.commit()
                    logger.info(f"AUDIT: Successfully deleted database record for file {original_filename} (ID: {record_id})")
                    
                    # Delete physical file if requested (after successful database commit)
                    if delete_physical_file and relative_path:
                        retry_count = 3
                        for attempt in range(retry_count):
                            try:
                                if self.file_storage.delete_file(relative_path):
                                    logger.info(f"AUDIT: Successfully deleted physical file {relative_path}")
                                    break
                                else:
                                    logger.warning(f"Physical file {relative_path} not found for deletion")
                            except Exception as file_error:
                                if attempt == retry_count - 1:
                                    logger.warning(f"Failed to delete physical file {relative_path} after {retry_count} attempts: {file_error}")
                                else:
                                    logger.warning(f"Retry {attempt + 1} deleting physical file {relative_path}: {file_error}")
                                    continue
                    
                    return True
                    
                except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                    # Rollback on any error
                    conn.rollback()
                    logger.error(f"AUDIT: Failed to delete file record {record_id}, rolled back: {e}")
                    return False
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error deleting file record {record_id}: {e}")
            return False
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error deleting file record {record_id}: {e}")
            return False
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error deleting file record {record_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file record {record_id}: {e}")
            return False
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get file statistics
        
        Returns:
            Dictionary with file statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Get total counts
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_files,
                        SUM(file_size) as total_bytes,
                        COUNT(CASE WHEN ingestion_status = 'completed' THEN 1 END) as completed_files,
                        COUNT(CASE WHEN ingestion_status = 'processing' THEN 1 END) as processing_files,
                        COUNT(CASE WHEN ingestion_status = 'error' THEN 1 END) as error_files,
                        COUNT(CASE WHEN ingestion_status = 'uploaded' THEN 1 END) as uploaded_files
                    FROM uploaded_files
                """)
                
                stats = dict(cursor.fetchone())
                
                # Get counts by file type
                cursor = conn.execute("""
                    SELECT mime_type, COUNT(*) as count
                    FROM uploaded_files
                    GROUP BY mime_type
                    ORDER BY count DESC
                """)
                
                stats["files_by_type"] = dict(cursor.fetchall())
                
                # Convert bytes to MB for readability
                if stats["total_bytes"]:
                    stats["total_mb"] = round(stats["total_bytes"] / (1024 * 1024), 2)
                else:
                    stats["total_mb"] = 0
                
                return stats
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error getting file stats: {e}")
            return {"error": f"Database operation failed: {str(e)}"}
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error getting file stats: {e}")
            return {"error": f"Database error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error getting file stats: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def cleanup_old_records(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old file records (for maintenance)
        
        Args:
            days: Number of days to keep records
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.db_manager.get_connection() as conn:
                try:
                    # Start transaction for cleanup
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Count records to be deleted
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM uploaded_files
                        WHERE created_at < ? AND ingestion_status IN ('completed', 'error')
                    """, (cutoff_date.isoformat(),))
                    
                    delete_count = cursor.fetchone()[0]
                    
                    if delete_count > 0:
                        # Delete old records (but keep physical files)
                        conn.execute("""
                            DELETE FROM uploaded_files
                            WHERE created_at < ? AND ingestion_status IN ('completed', 'error')
                        """, (cutoff_date.isoformat(),))
                        
                        conn.commit()
                    
                    logger.info(f"Cleaned up {delete_count} old file records")
                    
                    return {
                        "deleted_count": delete_count,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                    
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Database error during cleanup, rolled back: {e}")
                    raise RuntimeError(f"Cleanup transaction failed: {str(e)}")
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error during cleanup: {e}")
            return {"error": f"Database operation failed: {str(e)}", "deleted_count": 0}
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error during cleanup: {e}")
            return {"error": f"Database error: {str(e)}", "deleted_count": 0}
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")
            return {"error": f"Unexpected error: {str(e)}", "deleted_count": 0}
    
    def check_duplicate_exists(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if a file with the same hash already exists
        
        Args:
            file_hash: SHA256 hash to check
            
        Returns:
            File metadata if duplicate exists, None otherwise
        """
        return self.get_file_by_hash(file_hash)
    
    def get_active_processing_files(self) -> List[Dict[str, Any]]:
        """Get files that are currently being processed
        
        Returns:
            List of files with 'processing' status
        """
        return self.list_files_by_status(status="processing")


# Global file repository instance
file_repository = FileRepository()


def get_file_repository() -> FileRepository:
    """Get the global file repository instance"""
    return file_repository