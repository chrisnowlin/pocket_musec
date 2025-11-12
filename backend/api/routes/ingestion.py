from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os
import tempfile
import shutil
from pathlib import Path

from backend.ingestion.document_classifier import DocumentClassifier, DocumentType
from backend.pocketflow.ingestion_agent import IngestionAgent
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.repositories.database import DatabaseManager
from ..dependencies import get_current_user
from ...auth import User

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Initialize components
document_classifier = DocumentClassifier()


@router.post("/classify")
async def classify_document(file: UploadFile = File(...)):
    """Classify a document type"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

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
    file: UploadFile = File(...), advanced_option: Optional[str] = Form(None)
):
    """Ingest a document into the database"""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        try:
            # Classify document first
            doc_type, confidence = document_classifier.classify(tmp_file_path)

            # Create ingestion agent
            flow = Flow("Document Ingestion")
            store = Store()
            db_manager = DatabaseManager()
            agent = IngestionAgent(flow, store, db_manager=db_manager)

            # Initialize ingestion context
            agent.ingestion_context.update(
                {
                    "file_path": tmp_file_path,
                    "file_name": file.filename,
                    "document_type": doc_type,
                    "confidence": confidence,
                    "advanced_option": advanced_option,
                }
            )

            # Start ingestion
            try:
                # Clear existing data for this document type to avoid conflicts
                if doc_type.value == "unpacking":
                    with db_manager.get_connection() as conn:
                        conn.execute("DELETE FROM teaching_strategies")
                        conn.execute("DELETE FROM assessment_guidance")
                        conn.execute("DELETE FROM unpacking_sections")
                        conn.commit()
                elif doc_type.value == "standards":
                    with db_manager.get_connection() as conn:
                        conn.execute("DELETE FROM objectives")
                        conn.execute("DELETE FROM standards")
                        conn.commit()
                elif doc_type.value == "alignment":
                    with db_manager.get_connection() as conn:
                        conn.execute("DELETE FROM progression_mappings")
                        conn.execute("DELETE FROM alignment_relationships")
                        conn.commit()
                elif doc_type.value in ["glossary", "guide"]:
                    with db_manager.get_connection() as conn:
                        conn.execute("DELETE FROM resource_entries")
                        conn.execute("DELETE FROM faq_entries")
                        conn.execute("DELETE FROM glossary_entries")
                        conn.commit()

                result_message = agent._start_ingestion()

                # Get results
                results = agent.get_ingestion_results()

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "message": result_message,
                    }
                else:
                    return {"success": True, "results": {}, "message": result_message}

            except Exception as ingestion_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ingestion processing failed: {str(ingestion_error)}",
                )

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
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
