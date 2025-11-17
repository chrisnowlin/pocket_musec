"""Utilities for converting between snake_case and camelCase field names"""

import re
from typing import Dict, Any, Union, List


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

    # Insert underscore before capital letters and convert to lowercase
    snake = re.sub("([A-Z])", r"_\1", camel_str).lower()
    # Remove leading underscore if it exists
    return snake.lstrip("_")


def convert_dict_keys(
    data: Union[Dict[str, Any], List[Any]], to_camel: bool = True
) -> Union[Dict[str, Any], List[Any]]:
    """Convert dictionary keys between snake_case and camelCase"""
    if isinstance(data, list):
        return [convert_dict_keys(item, to_camel) for item in data]
    elif isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            # Convert the key
            new_key = snake_to_camel(key) if to_camel else camel_to_snake(key)

            # Recursively convert nested structures
            if isinstance(value, (dict, list)):
                converted[new_key] = convert_dict_keys(value, to_camel)
            else:
                converted[new_key] = value

        return converted
    else:
        return data


def convert_model_fields(model_obj: Any, to_camel: bool = True) -> Dict[str, Any]:
    """Convert model object fields between snake_case and camelCase"""
    if hasattr(model_obj, "model_dump") or hasattr(model_obj, "dict"):
        # Pydantic model
        data = (
            model_obj.model_dump()
            if hasattr(model_obj, "model_dump")
            else model_obj.dict()
        )
    else:
        # Regular object with __dict__
        data = {k: v for k, v in model_obj.__dict__.items() if not k.startswith("_")}

    result = convert_dict_keys(data, to_camel)
    if isinstance(result, dict):
        return result
    else:
        return {}


class FieldConverter:
    """Context-aware field converter that respects feature flags"""

    @staticmethod
    def should_use_camelcase() -> bool:
        """Check if camelCase should be used based on feature flags"""
        try:
            from config.feature_flags import feature_flags

            return feature_flags.is_enabled("CAMELCASE_API_RESPONSES")
        except ImportError:
            return False

    @staticmethod
    def should_maintain_compatibility() -> bool:
        """Check if snake_case compatibility should be maintained"""
        try:
            from config.feature_flags import feature_flags

            return feature_flags.is_enabled("SNAKECASE_COMPATIBILITY")
        except ImportError:
            return True

    @classmethod
    def convert_response(
        cls, data: Union[Dict[str, Any], List[Any]]
    ) -> Union[Dict[str, Any], List[Any]]:
        """Convert response data based on feature flags"""
        if cls.should_use_camelcase():
            return convert_dict_keys(data, to_camel=True)
        else:
            return data

    @classmethod
    def convert_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert request data based on feature flags"""
        # Always accept both formats during transition
        if cls.should_maintain_compatibility():
            # Try to detect if data is already camelCase or snake_case
            # and convert to the format expected by internal processing
            if cls.should_use_camelcase():
                # Internal processing expects camelCase
                if cls._is_snake_case_data(data):
                    result = convert_dict_keys(data, to_camel=True)
                    if isinstance(result, dict):
                        return result
                    else:
                        return {}
                else:
                    return data
            else:
                # Internal processing expects snake_case
                if cls._is_camel_case_data(data):
                    result = convert_dict_keys(data, to_camel=False)
                    if isinstance(result, dict):
                        return result
                    else:
                        return {}
                else:
                    return data
        return data

    @staticmethod
    def _is_snake_case_data(data: Dict[str, Any]) -> bool:
        """Check if dictionary keys are primarily snake_case"""
        if not data:
            return False

        snake_count = sum(1 for key in data.keys() if "_" in key)
        return snake_count > len(data) / 2

    @staticmethod
    def _is_camel_case_data(data: Dict[str, Any]) -> bool:
        """Check if dictionary keys are primarily camelCase"""
        if not data:
            return False

        camel_count = sum(1 for key in data.keys() if any(c.isupper() for c in key[1:]))
        return camel_count > len(data) / 2


# Common field mappings for quick reference
COMMON_FIELD_MAPPINGS = {
    # Session fields
    "user_id": "userId",
    "grade_level": "gradeLevel",
    "strand_code": "strandCode",
    "selected_standards": "selectedStandards",
    "selected_objectives": "selectedObjectives",
    "additional_standards": "additionalStandards",
    "additional_objectives": "additionalObjectives",
    "additional_context": "additionalContext",
    "lesson_duration": "lessonDuration",
    "class_size": "classSize",
    "agent_state": "agentState",
    "conversation_history": "conversationHistory",
    "current_state": "currentState",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    # Lesson fields
    "lesson_id": "lessonId",
    "lesson_title": "lessonTitle",
    "learning_objectives": "learningObjectives",
    "required_materials": "requiredMaterials",
    "standards_alignment": "standardsAlignment",
    "lesson_procedure": "lessonProcedure",
    "assessment_methods": "assessmentMethods",
    "differentiation_strategies": "differentiationStrategies",
    "extension_activities": "extensionActivities",
    "reference_sources": "referenceSources",
    # Image fields
    "file_path": "filePath",
    "file_size": "fileSize",
    "mime_type": "mimeType",
    "extracted_text": "extractedText",
    "vision_summary": "visionSummary",
    "ocr_confidence": "ocrConfidence",
    "last_accessed": "lastAccessed",
    "upload_date": "uploadDate",
    # Citation fields
    "citation_number": "citationNumber",
    "standard_title": "standardTitle",
    "standard_id": "standardId",
    "version_date": "versionDate",
    "page_number": "pageNumber",
    "author_name": "authorName",
    "document_title": "documentTitle",
    "publication_info": "publicationInfo",
    "publication_date": "publicationDate",
    "page_range": "pageRange",
    "image_title": "imageTitle",
    "image_type": "imageType",
    "uploaded_by": "uploadedBy",
}
