"""Data models for pocket_musec"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Standard:
    """Represents a music education standard"""
    standard_id: str
    grade_level: str
    strand_code: str
    strand_name: str
    strand_description: str
    standard_text: str
    source_document: Optional[str] = None
    ingestion_date: Optional[str] = None
    version: Optional[str] = None


@dataclass
class Objective:
    """Represents a learning objective within a standard"""
    objective_id: str
    standard_id: str
    objective_text: str


@dataclass
class StandardWithObjectives:
    """Standard with its associated objectives"""
    standard: Standard
    objectives: List[Objective]