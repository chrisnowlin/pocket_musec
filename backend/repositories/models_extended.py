"""Extended data models for unpacking, alignment, and reference documents"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


# Unpacking Document Models
@dataclass
class UnpackingSection:
    """Represents a section of unpacking content"""

    section_id: str
    grade_level: str
    strand_code: Optional[str]
    standard_id: Optional[str]
    section_title: str
    content: str
    page_number: int
    source_document: str
    ingestion_date: str
    version: str = "1.0"


@dataclass
class TeachingStrategy:
    """Represents a teaching strategy from unpacking documents"""

    strategy_id: str
    section_id: str
    strategy_text: str
    grade_level: str
    strand_code: Optional[str]
    standard_id: Optional[str]
    source_document: str
    page_number: int
    ingestion_date: str


@dataclass
class AssessmentGuidance:
    """Represents assessment guidance from unpacking documents"""

    guidance_id: str
    section_id: str
    guidance_text: str
    grade_level: str
    strand_code: Optional[str]
    standard_id: Optional[str]
    source_document: str
    page_number: int
    ingestion_date: str


# Alignment Document Models
@dataclass
class AlignmentRelationship:
    """Represents a relationship between standards"""

    relationship_id: str
    standard_id: str
    related_standard_ids: List[str]
    relationship_type: str  # 'horizontal', 'vertical', 'prerequisite', 'builds_on'
    grade_level: str
    strand_code: str
    description: str
    source_document: str
    page_number: int
    ingestion_date: str
    version: str = "1.0"


@dataclass
class ProgressionMapping:
    """Represents skill progression across grades"""

    mapping_id: str
    skill_name: str
    grade_levels: List[str]
    standard_mappings: Dict[str, str]  # grade -> standard_id
    progression_notes: str
    source_document: str
    page_number: int
    ingestion_date: str
    version: str = "1.0"


# Reference Document Models
@dataclass
class GlossaryEntry:
    """Represents a glossary term and definition"""

    entry_id: str
    term: str
    definition: str
    page_number: int
    related_standards: List[str]
    source_document: str
    ingestion_date: str
    version: str = "1.0"


@dataclass
class FAQEntry:
    """Represents a FAQ question and answer"""

    entry_id: str
    question: str
    answer: str
    page_number: int
    category: Optional[str]
    source_document: str
    ingestion_date: str
    version: str = "1.0"


@dataclass
class ResourceEntry:
    """Represents a general resource entry"""

    entry_id: str
    title: str
    description: str
    content_type: str  # 'glossary', 'faq', 'catalog', 'appendix'
    page_number: int
    metadata: Dict[str, Any]
    source_document: str
    ingestion_date: str
    version: str = "1.0"


# Helper functions for creating IDs
def generate_section_id(
    grade_level: str, section_title: str, page_number: int, content_hash: str = ""
) -> str:
    """Generate unique section ID"""
    import hashlib

    # Use content hash if provided to ensure uniqueness for generic titles
    if content_hash:
        content = f"{grade_level}_{section_title}_{page_number}_{content_hash}"
    else:
        content = f"{grade_level}_{section_title}_{page_number}"
    return f"section_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_strategy_id(section_id: str, strategy_text: str) -> str:
    """Generate unique strategy ID"""
    import hashlib

    content = f"{section_id}_{strategy_text[:50]}"
    return f"strategy_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_guidance_id(section_id: str, guidance_text: str) -> str:
    """Generate unique guidance ID"""
    import hashlib

    content = f"{section_id}_{guidance_text[:50]}"
    return f"guidance_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_relationship_id(
    standard_id: str, related_ids: List[str], relationship_type: str
) -> str:
    """Generate unique relationship ID"""
    import hashlib

    content = f"{standard_id}_{'_'.join(related_ids)}_{relationship_type}"
    return f"rel_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_mapping_id(skill_name: str, grade_levels: List[str]) -> str:
    """Generate unique mapping ID"""
    import hashlib

    content = f"{skill_name}_{'_'.join(grade_levels)}"
    return f"mapping_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_glossary_id(term: str, page_number: int) -> str:
    """Generate unique glossary entry ID"""
    import hashlib

    content = f"{term}_{page_number}"
    return f"gloss_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_faq_id(question: str, page_number: int) -> str:
    """Generate unique FAQ entry ID"""
    import hashlib

    content = f"{question}_{page_number}"
    return f"faq_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def generate_resource_id(title: str, content_type: str, page_number: int) -> str:
    """Generate unique resource entry ID"""
    import hashlib

    content = f"{title}_{content_type}_{page_number}"
    return f"resource_{hashlib.md5(content.encode()).hexdigest()[:8]}"
