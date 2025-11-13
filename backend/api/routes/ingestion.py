from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any
import os
import tempfile
import shutil
from pathlib import Path
import mimetypes
import logging
from datetime import datetime
import magic

from backend.ingestion.document_classifier import DocumentClassifier, DocumentType
from backend.pocketflow.ingestion_agent import IngestionAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.database import DatabaseManager
from backend.repositories.file_repository import FileRepository
from backend.utils.file_storage import FileStorageManager
from ..dependencies import get_current_user
from ...auth import User
from ...config import config

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Initialize components
document_classifier = DocumentClassifier()
file_storage = FileStorageManager()
file_repository = FileRepository()

logger = logging.getLogger(__name__)


@router.post("/classify")
async def classify_document(file: UploadFile = File(...)):
    """Classify a document type"""
    try:
        # Validate file has filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Basic extension check for classify endpoint (PDFs only)
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for classification")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
            
            # Validate actual file content
            try:
                with open(tmp_file_path, 'rb') as f:
                    header = f.read(4)
                    if not header:
                        raise HTTPException(status_code=400, detail="File appears to be empty")
                    
                    # Check PDF magic bytes
                    if header != b'%PDF':
                        detected_mime = magic.from_buffer(header, mime=True)
                        if detected_mime != 'application/pdf':
                            raise HTTPException(
                                status_code=400,
                                detail=f"File content does not match PDF format. Detected: {detected_mime}"
                            )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"File validation failed: {e}")
                raise HTTPException(status_code=400, detail="File validation failed")

        try:
            # Classify document
            doc_type, confidence = document_classifier.classify(tmp_file_path)
            recommended_parser = document_classifier.get_recommended_parser(doc_type)

            # Get document type info
            doc_type_info = {
                "value": doc_type.value,
                "label": _get_document_type_label(doc_type),
                "description": _get_document_type_description(doc_type),
                "icon": _get_document_type_icon(doc_type),
            }

            return {
                "success": True,
                "classification": {
                    "fileName": file.filename,
                    "documentType": doc_type_info,
                    "confidence": confidence,
                    "recommendedParser": recommended_parser,
                },
            }

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    advanced_option: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Ingest a document into the database with permanent file storage"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file_storage.is_allowed_extension(file.filename):
            allowed_exts = ", ".join(config.file_storage.allowed_extensions)
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed extensions: {allowed_exts}"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        file_record_id = None
        try:
            # Validate file size
            if not file_storage.is_valid_file_size(tmp_file_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed size of {config.file_storage.max_file_size} bytes"
                )
            
            # Calculate file hash for duplicate detection
            file_hash = file_storage.calculate_file_hash(tmp_file_path)
            
            # Check for duplicates if enabled
            duplicate_file = None
            if config.file_storage.duplicate_detection:
                duplicate_file = file_repository.check_duplicate_exists(file_hash)
                if duplicate_file:
                    logger.info(f"Duplicate file detected: {file.filename} matches existing file {duplicate_file['original_filename']}")
                    return {
                        "success": True,
                        "duplicate": True,
                        "message": "File already exists",
                        "existing_file": {
                            "id": duplicate_file["id"],
                            "filename": duplicate_file["original_filename"],
                            "upload_date": duplicate_file["created_at"],
                            "status": duplicate_file["ingestion_status"]
                        }
                    }
            
            # Save file permanently
            file_id, relative_path = file_storage.save_file_permanently(tmp_file_path, file.filename)
            
            # Get MIME type with enhanced content-based validation
            try:
                # First try to guess from filename
                filename_mime, _ = mimetypes.guess_type(file.filename)
                
                # Then validate with content-based detection
                with open(tmp_file_path, 'rb') as f:
                    # Read first few bytes for MIME detection
                    header = f.read(2048)  # Increased buffer size for better detection
                    if not header:
                        raise HTTPException(status_code=400, detail="File appears to be empty")
                    
                    # Use python-magic for accurate MIME type detection
                    detected_mime = magic.from_buffer(header, mime=True)
                    
                    # Validate the detected MIME type
                    if not detected_mime:
                        raise HTTPException(
                            status_code=400,
                            detail="Unable to determine file type - file may be corrupted or unsupported"
                        )
                    
                    # Check for suspicious or executable MIME types
                    suspicious_mimes = {
                        'application/x-executable',
                        'application/x-msdownload',
                        'application/x-msdos-program',
                        'application/x-sh',
                        'application/x-bat',
                        'application/x-python',
                        'application/javascript',
                        'application/x-javascript',
                        'text/javascript',
                        'application/x-msi',
                        'application/x-apple-diskimage',
                        'application/x-rar-compressed',
                        'application/x-7z-compressed'
                    }
                    
                    if detected_mime in suspicious_mimes:
                        logger.warning(f"Suspicious file type detected: {detected_mime}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Suspicious file type detected: {detected_mime}"
                        )
                    
                    # Validate MIME type is allowed with strict whitelist
                    allowed_mime_types = {
                        'application/pdf',
                        'text/plain',
                        'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'image/jpeg',
                        'image/png',
                        'image/tiff',
                        'image/gif',  # Added for completeness
                        'application/vnd.ms-word',  # Additional Word format
                        'application/rtf'  # Rich Text Format
                    }
                    
                    if detected_mime not in allowed_mime_types:
                        logger.warning(f"Unsupported file type: {detected_mime}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"File type not allowed. Detected MIME type: {detected_mime}"
                        )
                    
                    # Cross-validate filename extension with detected MIME type
                    if filename_mime:
                        # Check for major mismatches that indicate spoofed files
                        mime_mismatches = {
                            'application/pdf': ['.exe', '.bat', '.sh', '.js', '.zip'],
                            'application/msword': ['.exe', '.bat', '.sh', '.js', '.pdf'],
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.exe', '.bat', '.sh', '.js', '.pdf'],
                            'image/jpeg': ['.exe', '.bat', '.sh', '.js', '.pdf'],
                            'image/png': ['.exe', '.bat', '.sh', '.js', '.pdf'],
                            'text/plain': ['.exe', '.bat', '.sh', '.js', '.pdf']
                        }
                        
                        file_ext = Path(file.filename).suffix.lower()
                        if detected_mime in mime_mismatches and file_ext in mime_mismatches[detected_mime]:
                            logger.warning(f"Dangerous MIME/extension mismatch: {detected_mime} vs {file_ext}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"File extension {file_ext} does not match detected content type {detected_mime}"
                            )
                    
                    mime_type = detected_mime
                    logger.info(f"Validated MIME type for {file.filename}: {mime_type}")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"MIME type validation failed for {file.filename}: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"File type validation failed: {str(e)}"
                )
            
            # Get file size
            file_size = os.path.getsize(tmp_file_path)
            
            # Create database record
            file_record_id = file_repository.create_file_record(
                original_filename=file.filename,
                file_id=file_id,
                relative_path=relative_path,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                user_id=current_user.id if hasattr(current_user, 'id') else None,
                metadata={
                    "advanced_option": advanced_option,
                    "original_filename": file.filename
                }
            )
            
            # Update status to processing
            file_repository.update_ingestion_status(file_record_id, "processing")
            
            # Classify document
            doc_type, confidence = document_classifier.classify(tmp_file_path)

            # Create ingestion agent
            flow = Flow("Document Ingestion")
            store = Store()
            db_manager = DatabaseManager()
            agent = IngestionAgent(flow, store, db_manager=db_manager)

            # Initialize ingestion context with file storage info
            agent.ingestion_context.update(
                {
                    "file_path": tmp_file_path,
                    "file_name": file.filename,
                    "document_type": doc_type,
                    "confidence": confidence,
                    "advanced_option": advanced_option,
                    "file_record_id": file_record_id,
                    "file_id": file_id,
                    "relative_path": relative_path,
                    "file_hash": file_hash,
                }
            )

            # Start ingestion with enhanced transaction management and safety checks
            try:
                # Clear existing data for this document type to avoid conflicts
                # Use explicit transaction with rollback capability and validation
                with db_manager.get_connection() as conn:
                    try:
                        # Start explicit transaction with immediate locking
                        conn.execute("BEGIN IMMEDIATE")
                        
                        # Validate document type and get table mappings with whitelist
                        document_table_mappings = {
                            "unpacking": ["teaching_strategies", "assessment_guidance", "unpacking_sections"],
                            "standards": ["objectives", "standards"],
                            "alignment": ["progression_mappings", "alignment_relationships"],
                            "glossary": ["resource_entries", "faq_entries", "glossary_entries"],
                            "guide": ["resource_entries", "faq_entries", "glossary_entries"]
                        }
                        
                        if doc_type.value not in document_table_mappings:
                            logger.error(f"AUDIT: Invalid document type attempted: {doc_type.value}")
                            raise ValueError(f"Unsupported document type: {doc_type.value}")
                        
                        tables = document_table_mappings[doc_type.value]
                        
                        # Validate all table names exist and are safe
                        safe_tables = []
                        for table in tables:
                            # Check if table exists
                            cursor = conn.execute("""
                                SELECT name FROM sqlite_master
                                WHERE type='table' AND name=?
                            """, (table,))
                            if not cursor.fetchone():
                                logger.warning(f"Table {table} does not exist, skipping")
                                continue
                            safe_tables.append(table)
                        
                        if not safe_tables:
                            logger.info(f"No valid tables found for document type {doc_type.value}")
                        
                        # Log the deletion operation for audit trail
                        deleted_counts = {}
                        total_records_to_delete = 0
                        
                        # Count records before deletion for audit and safety check
                        for table in safe_tables:
                            try:
                                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                deleted_counts[table] = count
                                total_records_to_delete += count
                            except sqlite3.Error as e:
                                logger.error(f"Failed to count records in {table}: {e}")
                                deleted_counts[table] = 0
                        
                        # Safety check: warn if deleting large amounts of data
                        if total_records_to_delete > 10000:
                            logger.warning(f"AUDIT: Large deletion operation: {total_records_to_delete} records for {doc_type.value}")
                            # Log detailed audit info for large deletions
                            audit_details = {
                                "user_id": getattr(current_user, 'id', 'unknown'),
                                "document_type": doc_type.value,
                                "file_record_id": file_record_id,
                                "records_to_delete": deleted_counts,
                                "total_records": total_records_to_delete,
                                "timestamp": datetime.now().isoformat()
                            }
                            logger.warning(f"AUDIT: Large deletion operation details: {audit_details}")
                        
                        # Perform deletions with error handling for each table
                        deletion_errors = []
                        for table in safe_tables:
                            try:
                                cursor = conn.execute(f"DELETE FROM {table}")
                                actual_deleted = cursor.rowcount
                                if actual_deleted != deleted_counts[table]:
                                    logger.warning(f"Deletion count mismatch for {table}: expected {deleted_counts[table]}, actual {actual_deleted}")
                                    deleted_counts[table] = actual_deleted
                            except sqlite3.Error as e:
                                error_msg = f"Failed to delete from {table}: {str(e)}"
                                logger.error(error_msg)
                                deletion_errors.append(error_msg)
                        
                        # If any deletions failed, rollback
                        if deletion_errors:
                            raise Exception(f"Deletion errors: {'; '.join(deletion_errors)}")
                        
                        # Log audit information with details
                        audit_info = {
                            "document_type": doc_type.value,
                            "file_record_id": file_record_id,
                            "user_id": getattr(current_user, 'id', 'unknown'),
                            "deleted_records": deleted_counts,
                            "total_deleted": sum(deleted_counts.values()),
                            "timestamp": datetime.now().isoformat()
                        }
                        logger.info(f"AUDIT: Safe deletion completed: {audit_info}")
                        
                        # Commit the deletions
                        conn.commit()
                        
                    except (sqlite3.Error, ValueError, Exception) as delete_error:
                        # Rollback on any error with detailed logging
                        conn.rollback()
                        error_details = {
                            "document_type": doc_type.value,
                            "file_record_id": file_record_id,
                            "error": str(delete_error),
                            "timestamp": datetime.now().isoformat(),
                            "user_id": getattr(current_user, 'id', 'unknown')
                        }
                        logger.error(f"AUDIT: Deletion failed, rolled back: {error_details}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to clear existing data safely: {str(delete_error)}"
                        )

                result_message = agent._start_ingestion()

                # Get results
                results = agent.get_ingestion_results()

                # Update file record status to completed
                file_repository.update_ingestion_status(
                    file_record_id,
                    "completed",
                    metadata_update={
                        "document_type": doc_type.value,
                        "confidence": confidence,
                        "ingestion_results": results,
                        "processing_time": datetime.now().isoformat()
                    }
                )

                response_data = {
                    "success": True,
                    "results": results,
                    "message": result_message,
                    "file_metadata": {
                        "id": file_record_id,
                        "file_id": file_id,
                        "original_filename": file.filename,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "mime_type": mime_type,
                        "document_type": doc_type.value,
                        "confidence": confidence
                    }
                }

                if results:
                    response_data["results"] = results
                else:
                    response_data["results"] = {}

                return response_data

            except Exception as ingestion_error:
                # Update file record status to error
                error_msg = str(ingestion_error)
                file_repository.update_ingestion_status(file_record_id, "error", error_msg)
                raise HTTPException(
                    status_code=500,
                    detail=f"Ingestion processing failed: {error_msg}",
                )

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        # If we created a file record, update it with error
        if file_record_id:
            try:
                file_repository.update_ingestion_status(file_record_id, "error", str(e))
            except:
                pass  # Best effort, don't let this cause additional errors
        
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/document-types")
async def get_document_types():
    """Get supported document types"""
    return {
        "success": True,
        "documentTypes": [
            {
                "value": "standards",
                "label": "NC Music Standards",
                "description": "Formal standards documents with learning objectives",
                "icon": "📋",
            },
            {
                "value": "unpacking",
                "label": "Grade-Level Unpacking",
                "description": "Teaching strategies and assessment guidance",
                "icon": "📚",
            },
            {
                "value": "alignment",
                "label": "Alignment Matrices",
                "description": "Horizontal and vertical standard relationships",
                "icon": "🔗",
            },
            {
                "value": "glossary",
                "label": "Glossary & Reference",
                "description": "Definitions, FAQs, and resource materials",
                "icon": "📝",
            },
            {
                "value": "guide",
                "label": "Implementation Guides",
                "description": "Professional development and implementation resources",
                "icon": "📖",
            },
        ],
    }


@router.get("/advanced-options/{document_type}")
async def get_advanced_options(document_type: str):
    """Get advanced options for a specific document type"""
    try:
        doc_type = DocumentType(document_type)
        options = _get_advanced_options_for_type(doc_type)

        return {"success": True, "options": options}
    except ValueError:
        raise HTTPException(status_code=404, detail="Document type not found")


@router.get("/stats")
async def get_ingestion_stats():
    """Get ingestion statistics from the database"""
    try:
        # Initialize database connection
        db_manager = DatabaseManager()

        # Get counts from all tables
        stats = {}

        with db_manager.get_connection() as conn:
            # Standards tables
            try:
                stats["standards_count"] = conn.execute(
                    "SELECT COUNT(*) FROM standards"
                ).fetchone()[0]
            except:
                stats["standards_count"] = 0

            try:
                stats["objectives_count"] = conn.execute(
                    "SELECT COUNT(*) FROM objectives"
                ).fetchone()[0]
            except:
                stats["objectives_count"] = 0

            # Extended schema tables
            try:
                stats["sections_count"] = conn.execute(
                    "SELECT COUNT(*) FROM unpacking_sections"
                ).fetchone()[0]
            except:
                stats["sections_count"] = 0

            try:
                stats["strategies_count"] = conn.execute(
                    "SELECT COUNT(*) FROM teaching_strategies"
                ).fetchone()[0]
            except:
                stats["strategies_count"] = 0

            try:
                stats["guidance_count"] = conn.execute(
                    "SELECT COUNT(*) FROM assessment_guidance"
                ).fetchone()[0]
            except:
                stats["guidance_count"] = 0

            try:
                stats["relationships_count"] = conn.execute(
                    "SELECT COUNT(*) FROM alignment_relationships"
                ).fetchone()[0]
            except:
                stats["relationships_count"] = 0

            try:
                stats["mappings_count"] = conn.execute(
                    "SELECT COUNT(*) FROM progression_mappings"
                ).fetchone()[0]
            except:
                stats["mappings_count"] = 0

            try:
                stats["glossary_count"] = conn.execute(
                    "SELECT COUNT(*) FROM glossary_entries"
                ).fetchone()[0]
            except:
                stats["glossary_count"] = 0

            try:
                stats["faq_count"] = conn.execute(
                    "SELECT COUNT(*) FROM faq_entries"
                ).fetchone()[0]
            except:
                stats["faq_count"] = 0

            try:
                stats["resource_count"] = conn.execute(
                    "SELECT COUNT(*) FROM resource_entries"
                ).fetchone()[0]
            except:
                stats["resource_count"] = 0

        # Calculate total documents (approximate)
        stats["total_documents"] = stats.get("standards_count", 0)
        
        # Get the most recent ingestion date from any table
        try:
            last_updated = None
            # Check standards table
            result = conn.execute("""
                SELECT MAX(ingestion_date) FROM standards WHERE ingestion_date IS NOT NULL
            """).fetchone()
            if result and result[0]:
                last_updated = result[0]
            
            # Check other tables for more recent dates
            for table in ['objectives', 'teaching_strategies', 'assessment_guidance', 
                         'alignment_relationships', 'progression_mappings', 
                         'glossary_entries', 'faq_entries', 'resource_entries']:
                try:
                    result = conn.execute(f"""
                        SELECT MAX(ingestion_date) FROM {table} WHERE ingestion_date IS NOT NULL
                    """).fetchone()
                    if result and result[0]:
                        if not last_updated or result[0] > last_updated:
                            last_updated = result[0]
                except:
                    pass  # Table might not exist or have ingestion_date column
            
            stats["last_updated"] = last_updated or "2025-01-11T10:00:00Z"
        except:
            stats["last_updated"] = "2025-01-11T10:00:00Z"

        return {"success": True, "stats": stats}

    except Exception as e:
        # Return default stats on error
        default_stats = {
            "standards_count": 0,
            "objectives_count": 0,
            "sections_count": 0,
            "strategies_count": 0,
            "guidance_count": 0,
            "relationships_count": 0,
            "mappings_count": 0,
            "glossary_count": 0,
            "faq_count": 0,
            "resource_count": 0,
            "total_documents": 0,
            "last_updated": "2025-01-11T10:00:00Z",
        }
        return {"success": True, "stats": default_stats}


@router.get("/items/{content_type}")
async def get_content_items(
    content_type: str,
    limit: int = Query(100, gt=0, le=500),
    current_user: User = Depends(get_current_user),
):
    """Get detailed items for a specific content type"""
    import json
    
    db_manager = DatabaseManager()
    items = []
    
    try:
        with db_manager.get_connection() as conn:
            if content_type == "standards":
                cursor = conn.execute("""
                    SELECT standard_id, grade_level, strand_code, strand_name, 
                           standard_text, source_document, ingestion_date
                    FROM standards
                    ORDER BY grade_level, strand_code, standard_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "grade_level": row[1],
                        "strand_code": row[2],
                        "strand_name": row[3],
                        "text": row[4],
                        "source_document": row[5],
                        "ingestion_date": row[6],
                    })
            
            elif content_type == "objectives":
                cursor = conn.execute("""
                    SELECT objective_id, standard_id, objective_text
                    FROM objectives
                    ORDER BY standard_id, objective_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "standard_id": row[1],
                        "text": row[2],
                    })
            
            elif content_type == "strategies":
                cursor = conn.execute("""
                    SELECT strategy_id, section_id, grade_level, strand_code,
                           strategy_text, source_document, page_number
                    FROM teaching_strategies
                    ORDER BY grade_level, strand_code, strategy_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "section_id": row[1],
                        "grade_level": row[2],
                        "strand_code": row[3],
                        "text": row[4],
                        "source_document": row[5],
                        "page_number": row[6],
                    })
            
            elif content_type == "guidance":
                cursor = conn.execute("""
                    SELECT guidance_id, section_id, grade_level, strand_code,
                           guidance_text, source_document, page_number
                    FROM assessment_guidance
                    ORDER BY grade_level, strand_code, guidance_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "section_id": row[1],
                        "grade_level": row[2],
                        "strand_code": row[3],
                        "text": row[4],
                        "source_document": row[5],
                        "page_number": row[6],
                    })
            
            elif content_type == "relationships":
                cursor = conn.execute("""
                    SELECT relationship_id, standard_id, related_standard_ids,
                           relationship_type, grade_level, strand_code, description,
                           source_document, page_number
                    FROM alignment_relationships
                    ORDER BY grade_level, strand_code, relationship_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "standard_id": row[1],
                        "related_standard_ids": json.loads(row[2]) if row[2] else [],
                        "relationship_type": row[3],
                        "grade_level": row[4],
                        "strand_code": row[5],
                        "description": row[6],
                        "source_document": row[7],
                        "page_number": row[8],
                    })
            
            elif content_type == "mappings":
                cursor = conn.execute("""
                    SELECT mapping_id, skill_name, grade_levels, standard_mappings,
                           progression_notes, source_document, page_number
                    FROM progression_mappings
                    ORDER BY skill_name, mapping_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "skill_name": row[1],
                        "grade_levels": json.loads(row[2]) if row[2] else [],
                        "standard_mappings": json.loads(row[3]) if row[3] else {},
                        "progression_notes": row[4],
                        "source_document": row[5],
                        "page_number": row[6],
                    })
            
            elif content_type == "glossary":
                cursor = conn.execute("""
                    SELECT entry_id, term, definition, page_number, related_standards,
                           source_document
                    FROM glossary_entries
                    ORDER BY term
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "term": row[1],
                        "definition": row[2],
                        "page_number": row[3],
                        "related_standards": json.loads(row[4]) if row[4] else [],
                        "source_document": row[5],
                    })
            
            elif content_type == "faq":
                cursor = conn.execute("""
                    SELECT entry_id, question, answer, page_number, category,
                           source_document
                    FROM faq_entries
                    ORDER BY category, entry_id
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "question": row[1],
                        "answer": row[2],
                        "page_number": row[3],
                        "category": row[4],
                        "source_document": row[5],
                    })
            
            elif content_type == "resources":
                cursor = conn.execute("""
                    SELECT entry_id, resource_type, resource_name, description,
                           url, source_document, page_number
                    FROM resource_entries
                    ORDER BY resource_type, resource_name
                    LIMIT ?
                """, (limit,))
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "resource_type": row[1],
                        "resource_name": row[2],
                        "description": row[3],
                        "url": row[4],
                        "source_document": row[5],
                        "page_number": row[6],
                    })
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown content type: {content_type}. Valid types: standards, objectives, strategies, guidance, relationships, mappings, glossary, faq, resources"
                )
        
        return {"success": True, "items": items, "count": len(items)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch {content_type} items: {str(e)}"
        )


def _get_document_type_label(doc_type: DocumentType) -> str:
    """Get human-readable label for document type"""
    labels = {
        DocumentType.STANDARDS: "NC Music Standards",
        DocumentType.UNPACKING: "Grade-Level Unpacking",
        DocumentType.ALIGNMENT: "Alignment Matrices",
        DocumentType.GLOSSARY: "Glossary & Reference",
        DocumentType.GUIDE: "Implementation Guides",
        DocumentType.UNKNOWN: "Unknown Document",
    }
    return labels.get(doc_type, "Unknown Document")


def _get_document_type_description(doc_type: DocumentType) -> str:
    """Get description for document type"""
    descriptions = {
        DocumentType.STANDARDS: "Formal standards documents with learning objectives",
        DocumentType.UNPACKING: "Teaching strategies and assessment guidance",
        DocumentType.ALIGNMENT: "Horizontal and vertical standard relationships",
        DocumentType.GLOSSARY: "Definitions, FAQs, and resource materials",
        DocumentType.GUIDE: "Professional development and implementation resources",
        DocumentType.UNKNOWN: "Unrecognized document type",
    }
    return descriptions.get(doc_type, "Unrecognized document type")


def _get_document_type_icon(doc_type: DocumentType) -> str:
    """Get icon for document type"""
    icons = {
        DocumentType.STANDARDS: "📋",
        DocumentType.UNPACKING: "📚",
        DocumentType.ALIGNMENT: "🔗",
        DocumentType.GLOSSARY: "📝",
        DocumentType.GUIDE: "📖",
        DocumentType.UNKNOWN: "❓",
    }
    return icons.get(doc_type, "❓")


def _get_advanced_options_for_type(doc_type: DocumentType) -> list:
    """Get advanced options for document type"""
    options_map = {
        DocumentType.STANDARDS: [
            "Use vision AI processing (slower but more accurate)",
            "Use fast table-based processing",
            "Force re-ingestion (overwrite existing data)",
            "Preview extraction results",
        ],
        DocumentType.UNPACKING: [
            "Extract teaching strategies only",
            "Extract assessment examples only",
            "Extract all content sections",
        ],
        DocumentType.ALIGNMENT: [
            "Extract horizontal relationships only",
            "Extract vertical progressions only",
            "Extract all alignment data",
        ],
        DocumentType.GLOSSARY: [
            "Extract glossary terms only",
            "Extract FAQ entries only",
            "Extract all reference content",
        ],
        DocumentType.GUIDE: [
            "Extract glossary terms only",
            "Extract FAQ entries only",
            "Extract all reference content",
        ],
    }

    return options_map.get(doc_type, [])


@router.get("/files/{file_id}")
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get metadata for a specific file"""
    try:
        file_metadata = file_repository.get_file_by_id(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"success": True, "file": file_metadata}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a file by its ID"""
    try:
        file_metadata = file_repository.get_file_by_id(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the actual file path
        file_path = file_storage.get_file_path(
            file_metadata["file_id"],
            file_metadata["relative_path"]
        )
        
        if not file_storage.file_exists(file_metadata["relative_path"]):
            raise HTTPException(status_code=404, detail="Physical file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=file_metadata["original_filename"],
            media_type=file_metadata["mime_type"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get("/files")
async def list_files(
    status: Optional[str] = Query(None, description="Filter by ingestion status"),
    limit: int = Query(50, gt=0, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List files with optional status filter and pagination"""
    try:
        files = file_repository.list_files_by_status(status, limit, offset)
        
        # Get total count for pagination
        stats = file_repository.get_file_stats()
        total_count = stats.get("total_files", 0)
        
        return {
            "success": True,
            "files": files,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "count": len(files)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    delete_physical: bool = Query(True, description="Also delete the physical file"),
    confirm: bool = Query(False, description="Explicit confirmation required for destructive operations"),
    current_user: User = Depends(get_current_user)
):
    """Delete a file record and optionally the physical file with explicit confirmation"""
    try:
        # Require explicit confirmation for destructive operations
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Explicit confirmation required. Set confirm=true to proceed with deletion."
            )
        
        file_metadata = file_repository.get_file_by_id(file_id)
        
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Log the deletion attempt for audit trail
        logger.info(f"AUDIT: User {getattr(current_user, 'id', 'unknown')} attempting to delete file {file_id}: {file_metadata['original_filename']}")
        
        # Delete the file record and physical file with transaction management
        try:
            success = file_repository.delete_file_record(file_id, delete_physical)
            
            if success:
                logger.info(f"AUDIT: Successfully deleted file {file_id}: {file_metadata['original_filename']}")
                return {
                    "success": True,
                    "message": f"File {file_metadata['original_filename']} deleted successfully",
                    "deleted_physical_file": delete_physical,
                    "audit_log": f"File deletion performed by user {getattr(current_user, 'id', 'unknown')}"
                }
            else:
                logger.error(f"AUDIT: Failed to delete file {file_id}: {file_metadata['original_filename']}")
                raise HTTPException(status_code=500, detail="Failed to delete file")
                
        except Exception as delete_error:
            logger.error(f"AUDIT: Error during deletion of file {file_id}: {delete_error}")
            raise HTTPException(status_code=500, detail=f"Deletion failed: {str(delete_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUDIT: Unexpected error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/files/stats")
async def get_file_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get file storage statistics"""
    try:
        db_stats = file_repository.get_file_stats()
        storage_stats = file_storage.get_storage_stats()
        
        return {
            "success": True,
            "database_stats": db_stats,
            "storage_stats": storage_stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file statistics: {str(e)}")


@router.post("/files/cleanup")
async def cleanup_files(
    days: Optional[int] = Query(None, description="Override retention days"),
    confirm: bool = Query(False, description="Explicit confirmation required for cleanup operations"),
    current_user: User = Depends(get_current_user)
):
    """Clean up old files and records with explicit confirmation and detailed logging"""
    try:
        # Require explicit confirmation for bulk cleanup operations
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Explicit confirmation required for bulk cleanup. Set confirm=true to proceed."
            )
        
        retention_days = days or 30
        
        # Log cleanup attempt
        logger.info(f"AUDIT: User {getattr(current_user, 'id', 'unknown')} initiating cleanup of files older than {retention_days} days")
        
        try:
            # Clean up old records with transaction safety
            record_cleanup = file_repository.cleanup_old_records(retention_days)
            
            # Clean up old physical files
            physical_cleanup = file_storage.cleanup_old_files(retention_days)
            
            # Log successful cleanup
            logger.info(f"AUDIT: Cleanup completed - Records: {record_cleanup.get('deleted_count', 0)}, "
                       f"Files: {physical_cleanup.get('deleted_count', 0)}, "
                       f"User: {getattr(current_user, 'id', 'unknown')}")
            
            return {
                "success": True,
                "record_cleanup": record_cleanup,
                "physical_cleanup": physical_cleanup,
                "audit_log": f"Bulk cleanup performed by user {getattr(current_user, 'id', 'unknown')} with retention {retention_days} days"
            }
            
        except Exception as cleanup_error:
            logger.error(f"AUDIT: Cleanup operation failed for user {getattr(current_user, 'id', 'unknown')}: {cleanup_error}")
            raise HTTPException(status_code=500, detail=f"Cleanup operation failed: {str(cleanup_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUDIT: Unexpected error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup files: {str(e)}")


@router.get("/files/bulk")
async def get_bulk_file_metadata(
    file_ids: str = Query(..., description="Comma-separated list of file IDs"),
    current_user: User = Depends(get_current_user)
):
    """Get metadata for multiple files in bulk to avoid N+1 queries"""
    try:
        # Validate and parse file_ids parameter
        if not file_ids or not file_ids.strip():
            raise HTTPException(status_code=400, detail="No file IDs provided")
        
        # Split file IDs and validate limit
        file_id_list = [fid.strip() for fid in file_ids.split(',') if fid.strip()]
        if len(file_id_list) > 100:  # Prevent excessive queries
            raise HTTPException(status_code=400, detail="Too many file IDs requested (max 100)")
        
        if not file_id_list:
            raise HTTPException(status_code=400, detail="No valid file IDs provided")
        
        # Get file metadata in bulk using IN clause
        try:
            with file_repository.db_manager.get_connection() as conn:
                # Build placeholders for IN clause
                placeholders = ','.join(['?' for _ in file_id_list])
                
                cursor = conn.execute(f"""
                    SELECT id, file_id, original_filename, relative_path, file_hash,
                           file_size, mime_type, ingestion_status, created_at,
                           CASE
                               WHEN metadata LIKE '%document_type%' THEN
                                   json_extract(metadata, '$.document_type')
                               ELSE NULL
                           END as document_type
                    FROM uploaded_files
                    WHERE file_id IN ({placeholders})
                    ORDER BY created_at DESC
                """, file_id_list)
                
                files = [dict(row) for row in cursor.fetchall()]
                
                logger.info(f"Bulk file metadata request: {len(files)} files found for {len(file_id_list)} requested IDs")
                
                return {
                    "success": True,
                    "files": files,
                    "requested_count": len(file_id_list),
                    "found_count": len(files)
                }
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error in bulk file metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error in bulk file metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in bulk file metadata: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in bulk file metadata endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")
