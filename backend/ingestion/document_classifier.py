"""
Document type classifier for NC Music Education documents
Automatically detects document type and routes to appropriate parser
"""

import re
from pathlib import Path
from typing import Literal, Optional, Tuple
from enum import Enum
import logging

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of NC Music Education documents"""

    STANDARDS = "standards"  # Main standards document (table-based)
    UNPACKING = "unpacking"  # Grade-level unpacking documents (narrative)
    ALIGNMENT = "alignment"  # Horizontal/Vertical alignment documents
    GUIDE = "guide"  # Implementation guides, quick guides
    GLOSSARY = "glossary"  # Glossaries and reference documents
    SKILLS = "skills"  # Skills appendix
    UNKNOWN = "unknown"


class DocumentClassifier:
    """Classifier to detect NC Music Education document types"""

    # Filename patterns for quick classification
    FILENAME_PATTERNS = {
        DocumentType.STANDARDS: [
            r"final.*music.*ncscos",
            r"ncscos.*music",
            r"standards.*music",
            r"music.*standards",
        ],
        DocumentType.UNPACKING: [
            r"unpacking",
            r"grade.*unpacking",
            r"kindergarten.*gm",
            r"first.*grade.*gm",
            r"accomplished.*gm",
            r"intermediate.*vim",
            r"advanced.*vim",
        ],
        DocumentType.ALIGNMENT: [
            r"horizontal.*alignment",
            r"vertical.*alignment",
            r"alignment.*arts",
        ],
        DocumentType.GUIDE: [
            r"quick.*guide",
            r"implementation.*guide",
            r"teacher.*guide",
            r"vim.*guide",
            r"vimplementation",
        ],
        DocumentType.GLOSSARY: [
            r"glossary",
            r"faq",
            r"frequently.*asked",
        ],
        DocumentType.SKILLS: [r"skills.*appendix", r"music.*skills"],
    }

    # Content markers for verification
    CONTENT_MARKERS = {
        DocumentType.STANDARDS: [
            "Standard Course of Study",
            "K - 12 General Music",
            "North Carolina Arts Education Standards",
            "Note on Numbering",
            "Note on Strands",
        ],
        DocumentType.UNPACKING: [
            "Standards Unpacking",
            "Enduring Understanding",
            "Essential Questions",
            "In the Classroom",
            "Teaching Strategies",
            "Assessment Examples",
        ],
        DocumentType.GLOSSARY: [
            "Glossary",
            "Definition",
            "Term:",
            "Frequently Asked",
            "FAQ",
            "Q:",
            "A:",
        ],
        DocumentType.ALIGNMENT: [
            "Horizontal Alignment",
            "Vertical Alignment",
            "across grade levels",
            "progression of skills",
        ],
        DocumentType.GUIDE: [
            "Implementation Guide",
            "Quick Guide",
            "Getting Started",
            "Professional Development",
        ],
    }

    def classify_by_filename(self, filename: str) -> Optional[DocumentType]:
        """
        Classify document based on filename patterns

        Args:
            filename: Name of the PDF file

        Returns:
            DocumentType if matched, None otherwise
        """
        filename_lower = filename.lower()

        for doc_type, patterns in self.FILENAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    logger.debug(
                        f"Filename matched pattern '{pattern}' -> {doc_type.value}"
                    )
                    return doc_type

        return None

    def classify_by_content(self, pdf_path: str, max_pages: int = 5) -> DocumentType:
        """
        Classify document based on content analysis

        Args:
            pdf_path: Path to PDF file
            max_pages: Number of pages to analyze (default 5)

        Returns:
            DocumentType based on content markers
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available, cannot classify by content")
            return DocumentType.UNKNOWN

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from first few pages
                text_content = ""
                for i in range(min(max_pages, len(pdf.pages))):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        text_content += page_text + "\n"

                # Score each document type based on marker presence
                scores = {}
                for doc_type, markers in self.CONTENT_MARKERS.items():
                    score = sum(1 for marker in markers if marker in text_content)
                    scores[doc_type] = score

                # Return type with highest score
                if scores:
                    best_type = max(scores.items(), key=lambda x: x[1])[0]
                    if scores[best_type] > 0:
                        logger.debug(f"Content analysis scores: {scores}")
                        logger.info(
                            f"Classified as {best_type.value} (score: {scores[best_type]})"
                        )
                        return best_type

        except Exception as e:
            logger.error(f"Error during content classification: {e}")

        return DocumentType.UNKNOWN

    def classify(self, pdf_path: str) -> Tuple[DocumentType, float]:
        """
        Classify document using filename and content analysis

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (DocumentType, confidence_score)
            confidence_score: 0.0-1.0 where 1.0 is highest confidence
        """
        path = Path(pdf_path)

        # First try filename classification (fast)
        filename_type = self.classify_by_filename(path.name)

        if filename_type and filename_type != DocumentType.UNKNOWN:
            # Verify with content analysis
            content_type = self.classify_by_content(pdf_path)

            if filename_type == content_type:
                # Both agree - high confidence
                logger.info(
                    f"Document classified as {filename_type.value} (high confidence)"
                )
                return filename_type, 1.0
            elif content_type == DocumentType.UNKNOWN:
                # Content inconclusive, trust filename
                logger.info(
                    f"Document classified as {filename_type.value} (medium confidence - filename only)"
                )
                return filename_type, 0.7
            else:
                # Disagreement - trust content over filename
                logger.warning(
                    f"Filename suggested {filename_type.value} but content suggests {content_type.value}"
                )
                return content_type, 0.6
        else:
            # No filename match, rely on content
            content_type = self.classify_by_content(pdf_path)

            if content_type != DocumentType.UNKNOWN:
                logger.info(
                    f"Document classified as {content_type.value} (medium confidence - content only)"
                )
                return content_type, 0.6
            else:
                logger.warning(f"Could not confidently classify document: {path.name}")
                return DocumentType.UNKNOWN, 0.0

    def get_recommended_parser(self, doc_type: DocumentType) -> str:
        """
        Get recommended parser class for document type

        Args:
            doc_type: Classified document type

        Returns:
            Parser class name as string
        """
        parser_mapping = {
            DocumentType.STANDARDS: "NCStandardsParser",  # Uses table parser
            DocumentType.UNPACKING: "UnpackingParser",
            DocumentType.ALIGNMENT: "TextParser",  # Generic text parser
            DocumentType.GUIDE: "TextParser",
            DocumentType.SKILLS: "TextParser",
            DocumentType.UNKNOWN: "NCStandardsParser",  # Default fallback
        }

        return parser_mapping.get(doc_type, "NCStandardsParser")


def classify_document(pdf_path: str) -> Tuple[DocumentType, float, str]:
    """
    Convenience function to classify a document and get parser recommendation

    Args:
        pdf_path: Path to PDF file

    Returns:
        Tuple of (DocumentType, confidence, recommended_parser)
    """
    classifier = DocumentClassifier()
    doc_type, confidence = classifier.classify(pdf_path)
    parser = classifier.get_recommended_parser(doc_type)

    return doc_type, confidence, parser


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        doc_type, confidence, parser = classify_document(pdf_path)

        print(f"\nDocument: {pdf_path}")
        print(f"Type: {doc_type.value}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Recommended parser: {parser}")
    else:
        print("Usage: python document_classifier.py <pdf_path>")
