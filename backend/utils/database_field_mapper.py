"""Database field mapping utilities for camelCase migration

This module provides utilities for repositories to work with both snake_case
and camelCase database columns during the migration transition period.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case string to camelCase"""
    if not snake_str:
        return snake_str

    # Split on underscores and capitalize each part except the first
    parts = snake_str.split("_")
    if len(parts) == 1:
        return snake_str

    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase string to snake_case"""
    if not camel_str:
        return camel_str

    # Insert underscore before each capital letter (except the first)
    # and convert to lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class DatabaseFieldMapper:
    """Maps between snake_case and camelCase database fields"""

    # Common field mappings for all models
    COMMON_MAPPINGS = {
        "user_id": "userId",
        "session_id": "sessionId",
        "lesson_id": "lessonId",
        "grade_level": "gradeLevel",
        "strand_code": "strandCode",
        "strand_name": "strandName",
        "strand_description": "strandDescription",
        "standard_text": "standardText",
        "standard_id": "standardId",
        "objective_id": "objectiveId",
        "objective_text": "objectiveText",
        "source_document": "sourceDocument",
        "file_id": "fileId",
        "ingestion_date": "ingestionDate",
        "selected_standards": "selectedStandards",
        "selected_objectives": "selectedObjectives",
        "additional_standards": "additionalStandards",
        "additional_objectives": "additionalObjectives",
        "additional_context": "additionalContext",
        "lesson_duration": "lessonDuration",
        "class_size": "classSize",
        "selected_model": "selectedModel",
        "agent_state": "agentState",
        "conversation_history": "conversationHistory",
        "current_state": "currentState",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "last_login": "lastLogin",
        "password_hash": "passwordHash",
        "full_name": "fullName",
        "processing_mode": "processingMode",
        "is_active": "isActive",
        "is_draft": "isDraft",
        "source_type": "sourceType",
        "source_id": "sourceId",
        "source_title": "sourceTitle",
        "page_number": "pageNumber",
        "citation_text": "citationText",
        "citation_number": "citationNumber",
        "file_path": "filePath",
        "file_size": "fileSize",
        "mime_type": "mimeType",
        "extracted_text": "extractedText",
        "vision_summary": "visionSummary",
        "ocr_confidence": "ocrConfidence",
        "last_accessed": "lastAccessed",
    }

    def __init__(self):
        self.reverse_mappings = {v: k for k, v in self.COMMON_MAPPINGS.items()}

    def should_use_camelcase(self) -> bool:
        """Check if camelCase should be used based on feature flags"""
        return os.getenv("CAMELCASE_API_RESPONSES", "false").lower() == "true"

    def get_field_mapping(self, use_camelcase: Optional[bool] = None) -> Dict[str, str]:
        """Get field mapping for database operations"""
        if use_camelcase is None:
            use_camelcase = self.should_use_camelcase()

        if use_camelcase:
            return self.COMMON_MAPPINGS
        else:
            return {}

    def map_field_names(
        self, data: Dict[str, Any], to_camelcase: bool = False
    ) -> Dict[str, Any]:
        """Convert field names in data dictionary"""
        if not to_camelcase:
            return data

        mapped = {}
        for key, value in data.items():
            # Use predefined mapping if available, otherwise convert dynamically
            if key in self.COMMON_MAPPINGS:
                mapped[self.COMMON_MAPPINGS[key]] = value
            else:
                mapped[snake_to_camel(key)] = value
        return mapped

    def map_row_to_dict(self, row: Any, use_camelcase: bool = False) -> Dict[str, Any]:
        """Convert database row to dictionary with appropriate field names"""
        if hasattr(row, "keys"):
            # SQLite Row object
            data = {key: row[key] for key in row.keys()}
        else:
            # Regular tuple/dict
            data = dict(row) if not isinstance(row, dict) else row

        if use_camelcase:
            return self.map_field_names(data, to_camelcase=True)
        else:
            return data

    def build_select_clause(self, table_name: str, use_camelcase: bool = False) -> str:
        """Build SELECT clause with appropriate column aliases"""
        if not use_camelcase:
            return f"SELECT * FROM {table_name}"

        # For camelCase, we need to select both snake_case and camelCase columns
        # and prioritize camelCase columns when available
        camel_columns = list(self.COMMON_MAPPINGS.values())
        snake_columns = list(self.COMMON_MAPPINGS.keys())

        # Build a SELECT that prefers camelCase columns but falls back to snake_case
        select_parts = []
        for snake, camel in self.COMMON_MAPPINGS.items():
            select_parts.append(f"COALESCE({camel}, {snake}) AS {camel}")

        # Add any columns that don't have mappings
        select_parts.append("*")

        return f"SELECT {', '.join(select_parts)} FROM {table_name}"

    def build_insert_clause(
        self, table_name: str, data: Dict[str, Any], use_camelcase: bool = False
    ) -> Tuple[str, List[Any]]:
        """Build INSERT clause with appropriate column names"""
        if use_camelcase:
            mapped_data = self.map_field_names(data, to_camelcase=True)
        else:
            mapped_data = data

        columns = list(mapped_data.keys())
        placeholders = ["?" for _ in columns]
        values = list(mapped_data.values())

        sql = f"""
            INSERT INTO {table_name} ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
        """

        return sql.strip(), values

    def build_update_clause(
        self,
        table_name: str,
        data: Dict[str, Any],
        where_clause: str,
        where_params: List[Any],
        use_camelcase: bool = False,
    ) -> Tuple[str, List[Any]]:
        """Build UPDATE clause with appropriate column names"""
        if use_camelcase:
            mapped_data = self.map_field_names(data, to_camelcase=True)
        else:
            mapped_data = data

        set_clauses = [f"{key} = ?" for key in mapped_data.keys()]
        values = list(mapped_data.values()) + where_params

        sql = f"""
            UPDATE {table_name}
            SET {", ".join(set_clauses)}
            WHERE {where_clause}
        """

        return sql.strip(), values


# Global instance for reuse
field_mapper = DatabaseFieldMapper()


def map_repository_fields(
    data: Dict[str, Any], use_camelcase: bool = False
) -> Dict[str, Any]:
    """Convenience function to map repository fields"""
    return field_mapper.map_field_names(data, use_camelcase)


def build_camelcase_select(table_name: str) -> str:
    """Convenience function to build camelCase SELECT clause"""
    return field_mapper.build_select_clause(table_name, use_camelcase=True)


def should_use_camelcase() -> bool:
    """Convenience function to check if camelCase should be used"""
    return field_mapper.should_use_camelcase()
