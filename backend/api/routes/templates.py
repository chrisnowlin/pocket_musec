"""Templates management endpoints"""

import json
import uuid
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...repositories.database import DatabaseManager
from ..models import (
    TemplateResponse,
    TemplateCreateRequest,
    TemplateUpdateRequest,
)
from ..dependencies import get_current_user
from ...auth import User

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _get_template_table():
    """Get the templates table from database"""
    db_manager = DatabaseManager()
    db = db_manager.get_connection()
    cursor = db.cursor()
    
    # Create templates table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES auth_users (id)
        )
    """)
    db.commit()
    return db


def _row_to_template_response(row) -> TemplateResponse:
    """Convert a database row to a template response format"""
    
    # Parse metadata if available
    metadata = {}
    if row[4]:  # metadata column
        try:
            metadata = json.loads(row[4])
        except (json.JSONDecodeError, TypeError):
            metadata = {}
    
    return TemplateResponse(
        id=row[0],
        title=row[2],
        content=row[3],
        metadata=metadata,
        created_at=row[5],
        updated_at=row[6],
    )


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
) -> List[TemplateResponse]:
    """List all templates for the current user"""
    db = _get_template_table()
    cursor = db.cursor()
    
    # Get only templates for the user
    cursor.execute("""
        SELECT id, user_id, title, content, metadata, created_at, updated_at
        FROM templates 
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (current_user.id,))
    
    rows = cursor.fetchall()
    return [_row_to_template_response(row) for row in rows]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Get a specific template by ID"""
    db = _get_template_table()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT id, user_id, title, content, metadata, created_at, updated_at
        FROM templates 
        WHERE id = ? AND user_id = ?
    """, (template_id, current_user.id))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Template not found"
        )
    
    return _row_to_template_response(row)


@router.post("", response_model=TemplateResponse)
async def create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Create a new template"""
    db = _get_template_table()
    cursor = db.cursor()
    
    template_id = str(uuid.uuid4())
    metadata_json = json.dumps(request.metadata) if request.metadata else None
    
    cursor.execute("""
        INSERT INTO templates (id, user_id, title, content, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (template_id, current_user.id, request.title, request.content, metadata_json))
    
    db.commit()
    
    # Get the created template
    cursor.execute("""
        SELECT id, user_id, title, content, metadata, created_at, updated_at
        FROM templates 
        WHERE id = ?
    """, (template_id,))
    
    row = cursor.fetchone()
    return _row_to_template_response(row)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Update an existing template"""
    db = _get_template_table()
    cursor = db.cursor()
    
    # Check if template exists and belongs to user
    cursor.execute("""
        SELECT id, user_id, title, content, metadata, created_at, updated_at
        FROM templates 
        WHERE id = ? AND user_id = ?
    """, (template_id, current_user.id))
    
    existing_row = cursor.fetchone()
    if not existing_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Template not found"
        )
    
    # Build update query
    update_fields = []
    update_values = []
    
    if request.title is not None:
        update_fields.append("title = ?")
        update_values.append(request.title)
    
    if request.content is not None:
        update_fields.append("content = ?")
        update_values.append(request.content)
    
    if request.metadata is not None:
        metadata_json = json.dumps(request.metadata)
        update_fields.append("metadata = ?")
        update_values.append(metadata_json)
    
    if not update_fields:
        # No changes to make
        return _row_to_template_response(existing_row)
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    update_values.append(template_id)
    
    cursor.execute(f"""
        UPDATE templates 
        SET {', '.join(update_fields)}
        WHERE id = ?
    """, update_values)
    
    db.commit()
    
    # Get the updated template
    cursor.execute("""
        SELECT id, user_id, title, content, metadata, created_at, updated_at
        FROM templates 
        WHERE id = ?
    """, (template_id,))
    
    row = cursor.fetchone()
    return _row_to_template_response(row)


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a template"""
    db = _get_template_table()
    cursor = db.cursor()
    
    # Check if template exists and belongs to user
    cursor.execute("""
        SELECT id FROM templates 
        WHERE id = ? AND user_id = ?
    """, (template_id, current_user.id))
    
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Template not found"
        )
    
    # Delete the template
    cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    db.commit()
    
    return {"message": "Template deleted successfully"}