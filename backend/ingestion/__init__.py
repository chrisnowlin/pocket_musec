"""PDF ingestion components for pocket_musec"""

# Standards parsers
from .nc_standards_formal_parser import NCStandardsParser as FormalStandardsParser
from .nc_standards_table_parser import NCStandardsParser as TableStandardsParser
from .nc_standards_structured_parser import (
    NCStandardsParser as StructuredStandardsParser,
)
from .nc_standards_precise_parser import NCStandardsParser as PreciseStandardsParser
from .nc_standards_positional_parser import (
    NCStandardsParser as PositionalStandardsParser,
)

# Layout parsers
from .complex_layout_parser import NCStandardsParser as ComplexLayoutParser
from .simple_layout_parser import NCStandardsParser as SimpleLayoutParser

# Document-specific parsers
from .unpacking_narrative_parser import UnpackingNarrativeParser
from .reference_resource_parser import ReferenceResourceParser
from .alignment_matrix_parser import AlignmentMatrixParser

# Utilities
from .pdf_parser import PDFReader
from .document_classifier import DocumentClassifier, DocumentType

__all__ = [
    # Standards parsers
    "FormalStandardsParser",
    "TableStandardsParser",
    "StructuredStandardsParser",
    "PreciseStandardsParser",
    "PositionalStandardsParser",
    # Layout parsers
    "ComplexLayoutParser",
    "SimpleLayoutParser",
    # Document-specific parsers
    "UnpackingNarrativeParser",
    "ReferenceResourceParser",
    "AlignmentMatrixParser",
    # Utilities
    "PDFReader",
    "DocumentClassifier",
    "DocumentType",
]
