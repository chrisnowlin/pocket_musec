"""Citation formatter for IEEE and other styles"""

from enum import Enum
from typing import List, Dict
from .citation_tracker import SourceReference
import logging

logger = logging.getLogger(__name__)


class CitationStyle(str, Enum):
    """Citation style enumerations"""
    IEEE = "ieee"
    APA = "apa"
    MLA = "mla"


class CitationFormatter:
    """
    Formats citations in various styles

    Currently supports IEEE style, with hooks for APA and MLA
    """

    def __init__(self, style: CitationStyle = CitationStyle.IEEE):
        self.style = style

    def format_inline_citation(self, citation_number: int) -> str:
        """
        Format inline citation

        Args:
            citation_number: Citation number

        Returns:
            Formatted inline citation
        """
        if self.style == CitationStyle.IEEE:
            return f"[{citation_number}]"
        elif self.style == CitationStyle.APA:
            # Placeholder for APA style
            return f"({citation_number})"
        elif self.style == CitationStyle.MLA:
            # Placeholder for MLA style
            return f"({citation_number})"
        else:
            return f"[{citation_number}]"

    def format_inline_citations(self, citation_numbers: List[int]) -> str:
        """
        Format multiple inline citations

        Args:
            citation_numbers: List of citation numbers

        Returns:
            Formatted inline citations (e.g., [1, 3, 5] or [1-3])
        """
        if not citation_numbers:
            return ""

        # Sort and deduplicate
        numbers = sorted(set(citation_numbers))

        if len(numbers) == 1:
            return self.format_inline_citation(numbers[0])

        if self.style == CitationStyle.IEEE:
            # Check if contiguous for range notation
            if len(numbers) > 2 and numbers[-1] - numbers[0] == len(numbers) - 1:
                return f"[{numbers[0]}-{numbers[-1]}]"
            else:
                return f"[{', '.join(str(n) for n in numbers)}]"

        return self.format_inline_citation(numbers[0])  # Fallback

    def format_reference(self, source: SourceReference, citation_number: int) -> str:
        """
        Format full reference for bibliography

        Args:
            source: Source reference
            citation_number: Citation number

        Returns:
            Formatted reference string
        """
        if self.style == CitationStyle.IEEE:
            return self._format_ieee_reference(source, citation_number)
        elif self.style == CitationStyle.APA:
            return self._format_apa_reference(source, citation_number)
        elif self.style == CitationStyle.MLA:
            return self._format_mla_reference(source, citation_number)
        else:
            return self._format_ieee_reference(source, citation_number)

    def _format_ieee_reference(self, source: SourceReference, number: int) -> str:
        """Format reference in IEEE style"""

        if source.source_type == "standard":
            # Format: [#] Organization, "Standard ID: Title," Version/Date, p. Page.
            ref = f"[{number}] North Carolina Standard Course of Study, \"{source.source_id}: {source.source_title}\""

            if source.page_number:
                ref += f", p. {source.page_number}"

            ref += "."
            return ref

        elif source.source_type == "objective":
            # Format: [#] Organization, "Objective ID: Title," Version/Date.
            ref = f"[{number}] North Carolina Standard Course of Study, \"{source.source_id}: {source.source_title}\"."
            return ref

        elif source.source_type == "document":
            # Format: [#] Author, "Document Title," Publication, Date, pp. Pages.
            ref = f"[{number}] \"{source.source_title}\""

            if source.page_number:
                ref += f", p. {source.page_number}"

            ref += "."
            return ref

        elif source.source_type == "image":
            # Format: [#] "Title," Image Type, uploaded by Author, Upload Date.
            ref = f"[{number}] \"{source.source_title}\", Image"

            if source.page_number:
                ref += f", p. {source.page_number}"

            ref += "."
            return ref

        elif source.source_type == "web":
            # Format: [#] "Title," Domain Name, URL.
            ref = f"[{number}] \"{source.source_title}\""
            
            # Add domain information if available
            if hasattr(source, 'domain') and source.domain:
                display_domain = source.domain.replace('www.', '')
                ref += f", {display_domain}"
                
            # Add URL for web sources
            if hasattr(source, 'url') and source.url:
                ref += f", {source.url}"
                
            ref += "."
            return ref
            
        else:
            # Generic format
            ref = f"[{number}] {source.source_title}"
            if source.page_number:
                ref += f", p. {source.page_number}"
            ref += "."
            return ref

    def _format_apa_reference(self, source: SourceReference, number: int) -> str:
        """Format reference in APA style (placeholder)"""
        # TODO: Implement full APA formatting
        return f"({number}) {source.source_title}."

    def _format_mla_reference(self, source: SourceReference, number: int) -> str:
        """Format reference in MLA style (placeholder)"""
        # TODO: Implement full MLA formatting
        return f"{source.source_title}."

    def format_bibliography(
        self,
        sources: List[SourceReference],
        citation_map: Dict[str, int]
    ) -> str:
        """
        Format complete bibliography

        Args:
            sources: List of source references
            citation_map: Mapping of source_id to citation_number

        Returns:
            Formatted bibliography as markdown text
        """
        if not sources:
            return ""

        # Sort by citation number
        sorted_sources = sorted(
            sources,
            key=lambda src: citation_map.get(src.source_id, 999)
        )

        # Format each reference
        lines = ["## References\n"]

        for source in sorted_sources:
            citation_number = citation_map.get(source.source_id, 0)
            reference = self.format_reference(source, citation_number)
            lines.append(reference)

        return "\n".join(lines)

    def insert_citations_in_text(
        self,
        text: str,
        citation_markers: List[tuple]  # List of (position, citation_numbers)
    ) -> str:
        """
        Insert inline citations into text

        Args:
            text: Original text
            citation_markers: List of (position, [citation_numbers])

        Returns:
            Text with inline citations inserted
        """
        # Sort markers by position (reverse order to insert from end)
        sorted_markers = sorted(citation_markers, key=lambda x: x[0], reverse=True)

        result = text

        for position, citation_numbers in sorted_markers:
            citation_text = self.format_inline_citations(citation_numbers)
            # Insert after the position
            result = result[:position] + " " + citation_text + result[position:]

        return result

    def validate_citations(
        self,
        text: str,
        expected_citations: List[int]
    ) -> Dict[str, list]:
        """
        Validate that all expected citations are present

        Args:
            text: Text with citations
            expected_citations: List of expected citation numbers

        Returns:
            Dictionary with 'missing' and 'orphaned' citation lists
        """
        import re

        # Find all citations in text
        if self.style == CitationStyle.IEEE:
            pattern = r'\[(\d+(?:[-,]\d+)*)\]'
        else:
            pattern = r'\((\d+)\)'

        found_citations = set()

        for match in re.finditer(pattern, text):
            citation_str = match.group(1)
            # Parse ranges and lists
            if '-' in citation_str:
                start, end = map(int, citation_str.split('-'))
                found_citations.update(range(start, end + 1))
            elif ',' in citation_str:
                found_citations.update(map(int, citation_str.split(',')))
            else:
                found_citations.add(int(citation_str))

        expected_set = set(expected_citations)

        return {
            "missing": list(expected_set - found_citations),
            "orphaned": list(found_citations - expected_set)
        }
