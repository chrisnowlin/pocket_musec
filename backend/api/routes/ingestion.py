from fastapi import APIRouter, UploadFile, File, HTTPException, Form
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
        stats["last_updated"] = "2025-01-11T10:00:00Z"  # Would be dynamic in production

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
