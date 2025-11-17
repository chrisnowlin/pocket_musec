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


def format_grade_for_storage(display_grade: Optional[str]) -> Optional[str]:
    """Convert user-friendly grade labels back to database-compatible format"""
    if not display_grade:
        return display_grade

    normalized = display_grade.strip()

    # Handle kindergarten variations - frontend expects "K"
    if normalized.lower() in {"kindergarten", "k"}:
        return "K"  # Database format for kindergarten (matches frontend expectation)

    # Handle "Grade X" format - extract the number
    if normalized.startswith("Grade "):
        grade_num = normalized.replace("Grade ", "").strip()
        if grade_num.isdigit():
            return grade_num

    # Handle old format names ("First Grade", "Second Grade", etc.)
    reverse_grade_mapping = {
        "First Grade": "1",
        "Second Grade": "2",
        "Third Grade": "3",
        "Fourth Grade": "4",
        "Fifth Grade": "5",
        "Sixth Grade": "6",
        "Seventh Grade": "7",
        "Eighth Grade": "8",
    }

    # If it's in the mapping, convert it
    if normalized in reverse_grade_mapping:
        return reverse_grade_mapping[normalized]

    # If it's already a number, return as-is
    if normalized.isdigit():
        return normalized

    # All other cases return as-is
    return display_grade
