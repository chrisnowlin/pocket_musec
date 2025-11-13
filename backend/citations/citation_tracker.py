"""Citation tracker for recording source provenance during lesson generation"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    """Reference to a source used in generation"""
    source_type: str  # 'standard', 'objective', 'document', 'image'
    source_id: str
    source_title: str
    page_number: Optional[int] = None
    excerpt: Optional[str] = None
    relevance_score: float = 1.0  # 0-1, higher = more relevant
    file_id: Optional[str] = None  # File ID for source tracking


@dataclass
class CitationContext:
    """Context for a citation in generated content"""
    section: str  # Which section of lesson (e.g., "objectives", "activities")
    position: int  # Character position in content
    sources: List[SourceReference] = field(default_factory=list)


class CitationTracker:
    """
    Tracks sources during lesson generation

    Maintains provenance information for RAG-retrieved content
    """

    def __init__(self):
        self.sources: Dict[str, SourceReference] = {}  # source_id -> SourceReference
        self.citation_contexts: List[CitationContext] = []
        self.next_citation_number = 1
        self.citation_map: Dict[str, int] = {}  # source_id -> citation_number

    def add_source(
        self,
        source_type: str,
        source_id: str,
        source_title: str,
        page_number: Optional[int] = None,
        excerpt: Optional[str] = None,
        relevance_score: float = 1.0,
        file_id: Optional[str] = None
    ) -> int:
        """
        Add a source reference

        Args:
            source_type: Type of source
            source_id: Unique source identifier
            source_title: Human-readable title
            page_number: Page number (if applicable)
            excerpt: Relevant text excerpt
            relevance_score: Relevance score (0-1)
            file_id: File ID for source tracking

        Returns:
            Citation number assigned to this source
        """
        # Check if source already tracked
        if source_id in self.citation_map:
            logger.debug(f"Source {source_id} already tracked as citation #{self.citation_map[source_id]}")
            return self.citation_map[source_id]

        # Create source reference
        source_ref = SourceReference(
            source_type=source_type,
            source_id=source_id,
            source_title=source_title,
            page_number=page_number,
            excerpt=excerpt,
            relevance_score=relevance_score,
            file_id=file_id
        )

        # Assign citation number
        citation_number = self.next_citation_number
        self.citation_map[source_id] = citation_number
        self.sources[source_id] = source_ref
        self.next_citation_number += 1

        logger.info(f"Added source {source_id} as citation #{citation_number}")

        return citation_number

    def add_citation_context(
        self,
        section: str,
        position: int,
        source_ids: List[str]
    ) -> None:
        """
        Add citation context for a specific location

        Args:
            section: Section name (e.g., "objectives", "activities")
            position: Character position in content
            source_ids: List of source IDs contributing to this content
        """
        sources = [self.sources[sid] for sid in source_ids if sid in self.sources]

        context = CitationContext(
            section=section,
            position=position,
            sources=sources
        )

        self.citation_contexts.append(context)

        logger.debug(f"Added citation context at {section}:{position} with {len(sources)} sources")

    def get_citation_number(self, source_id: str) -> Optional[int]:
        """Get citation number for a source"""
        return self.citation_map.get(source_id)

    def get_all_sources(self) -> List[SourceReference]:
        """Get all tracked sources ordered by citation number"""
        return [
            self.sources[source_id]
            for source_id in sorted(self.citation_map.keys(), key=lambda x: self.citation_map[x])
        ]

    def get_sources_by_section(self, section: str) -> List[SourceReference]:
        """Get all sources cited in a specific section"""
        source_ids: Set[str] = set()

        for context in self.citation_contexts:
            if context.section == section:
                source_ids.update(src.source_id for src in context.sources)

        return [self.sources[sid] for sid in source_ids if sid in self.sources]

    def get_citation_count(self) -> int:
        """Get total number of unique citations"""
        return len(self.sources)

    def deduplicate_sources(self) -> None:
        """
        Deduplicate sources with same content

        Keeps the one with highest relevance score
        """
        # Group by (source_type, source_id)
        groups: Dict[tuple, List[str]] = {}

        for source_id, source_ref in self.sources.items():
            key = (source_ref.source_type, source_ref.source_id)
            if key not in groups:
                groups[key] = []
            groups[key].append(source_id)

        # For each group with duplicates, keep only the best one
        for key, source_ids in groups.items():
            if len(source_ids) > 1:
                # Find best source (highest relevance)
                best_id = max(
                    source_ids,
                    key=lambda sid: self.sources[sid].relevance_score
                )

                # Remove others
                for sid in source_ids:
                    if sid != best_id:
                        del self.sources[sid]
                        del self.citation_map[sid]

                logger.info(f"Deduplicated {len(source_ids)} sources for {key}, kept {best_id}")

    def to_dict(self) -> Dict:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation
        """
        return {
            "sources": {
                sid: {
                    "citation_number": self.citation_map[sid],
                    "source_type": src.source_type,
                    "source_id": src.source_id,
                    "source_title": src.source_title,
                    "page_number": src.page_number,
                    "excerpt": src.excerpt,
                    "relevance_score": src.relevance_score,
                    "file_id": src.file_id
                }
                for sid, src in self.sources.items()
            },
            "citation_count": len(self.sources)
        }

    def reset(self) -> None:
        """Reset tracker for new generation"""
        self.sources.clear()
        self.citation_contexts.clear()
        self.citation_map.clear()
        self.next_citation_number = 1
