"""Citation formatting and management endpoints"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..models import CamelModel
from backend.auth import User
from backend.citations.citation_formatter import CitationFormatter, CitationStyle
from backend.citations.citation_tracker import CitationTracker, SourceReference

router = APIRouter(prefix="/api/citations", tags=["citations"])


class CitationRequest(CamelModel):
    """Request for citation formatting"""

    sources: List[Dict[str, Any]]
    format: str = "ieee"


class CitationResponse(CamelModel):
    """Response containing formatted citations"""

    citations: List[str]
    metadata: Dict[str, Any]


class CitationSource(CamelModel):
    """Individual citation source"""

    title: str
    author: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    pages: Optional[str] = None


@router.post("/format", response_model=CitationResponse)
async def format_citations(
    request: CitationRequest,
    current_user: User = Depends(get_current_user),
) -> CitationResponse:
    """Format citations according to specified style"""
    try:
        # Determine citation style
        style_str = request.format.upper()
        if style_str not in [s.name for s in CitationStyle]:
            style_str = "IEEE"

        formatter = CitationFormatter(style=CitationStyle[style_str])

        # Convert request sources to citation format
        formatted_citations = []
        for i, source in enumerate(request.sources, 1):
            # Create a SourceReference from the source data
            source_ref = SourceReference(
                source_type="document",
                source_id=source.get("id", f"source_{i}"),
                source_title=source.get("title", "Untitled Source"),
                excerpt=source.get("excerpt"),
            )
            citation = formatter.format_reference(source_ref, i)
            formatted_citations.append(citation)

        return CitationResponse(
            citations=formatted_citations,
            metadata={
                "format": request.format,
                "count": len(formatted_citations),
                "formatted_by": "PocketMusec Citation Formatter",
            },
        )

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to format citations: {str(e)}",
        )


@router.post("/track")
async def track_citations(
    lesson_id: str,
    sources: List[CitationSource],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Track citations for a specific lesson"""
    try:
        tracker = CitationTracker()

        # Add citations to tracker using available methods
        citation_numbers = []
        for i, source in enumerate(sources):
            citation_num = tracker.add_source(
                source_type="document",
                source_id=f"{lesson_id}_source_{i}",
                source_title=source.title,
                excerpt=f"Author: {source.author or 'Unknown'}, Year: {source.year or 'Unknown'}",
            )
            citation_numbers.append(citation_num)

        return {
            "lesson_id": lesson_id,
            "citation_count": len(citation_numbers),
            "citation_numbers": citation_numbers,
            "tracked": True,
        }

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track citations: {str(e)}",
        )


@router.get("/lesson/{lesson_id}")
async def get_lesson_citations(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get all citations for a specific lesson"""
    try:
        # This is a simplified implementation
        # In production, you'd retrieve from database
        return [
            {
                "lesson_id": lesson_id,
                "message": "Citation retrieval not yet fully implemented",
                "status": "pending",
            }
        ]

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve citations: {str(e)}",
        )


@router.get("/formats")
async def get_available_formats(
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """Get list of available citation formats"""
    try:
        # Return supported formats from the enum
        return [style.value for style in CitationStyle]

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get citation formats: {str(e)}",
        )
