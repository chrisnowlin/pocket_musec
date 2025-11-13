"""Helpers for standards metadata formatting"""

from typing import Optional


def format_grade_display(grade_value: Optional[str]) -> Optional[str]:
    """Convert stored grade codes to user-friendly labels"""
    if not grade_value:
        return grade_value

    normalized = grade_value.strip()

    # Handle kindergarten variations (case-insensitive)
    # Database uses "K" as level_code, but level_name should be "Kindergarten"
    normalized_lower = normalized.lower()
    if normalized_lower in {"0", "k", "kindergarten"}:
        return "Kindergarten"

    # Handle numeric grades (legacy format)
    if normalized.isdigit():
        # Special case: "0" is Kindergarten
        if normalized == "0":
            return "Kindergarten"
        return f"Grade {normalized}"

    # Handle new format grade names ("First Grade", "Second Grade", etc.)
    grade_mapping = {
        "First Grade": "Grade 1",
        "Second Grade": "Grade 2",
        "Third Grade": "Grade 3",
        "Fourth Grade": "Grade 4",
        "Fifth Grade": "Grade 5",
        "Sixth Grade": "Grade 6",
        "Seventh Grade": "Grade 7",
        "Eighth Grade": "Grade 8",
    }

    # If it's in the mapping, convert it
    if normalized in grade_mapping:
        return grade_mapping[normalized]

    # For proficiency levels and other formats, return as-is
    return grade_value
