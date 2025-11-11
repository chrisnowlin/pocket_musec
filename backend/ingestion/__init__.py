"""PDF ingestion components for pocket_musec"""

# Standards parsers
from .nc_standards_unified_parser import NCStandardsParser, ParsingStrategy

# Layout parsers
from .complex_layout_parser import NCStandardsParser as ComplexLayoutParser
from .simple_layout_parser import SimpleLayoutParser

# Document-specific parsers
from .unpacking_narrative_parser import UnpackingNarrativeParser
from .reference_resource_parser import ReferenceResourceParser
from .alignment_matrix_parser import AlignmentMatrixParser

# Utilities
from .pdf_parser import PDFReader
from .document_classifier import DocumentClassifier, DocumentType

__all__ = [
    # Standards parsers
    "NCStandardsParser",  # New unified parser
    "ParsingStrategy",    # Strategy enum for unified parser
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
