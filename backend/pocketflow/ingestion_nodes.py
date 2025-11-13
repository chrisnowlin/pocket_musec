"""Ingestion workflow nodes for PocketFlow framework"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import sqlite3
import logging

from .node import Node
from ..ingestion.document_classifier import DocumentClassifier, DocumentType
from ..ingestion.nc_standards_unified_parser import NCStandardsParser, ParsingStrategy
from ..ingestion.unpacking_narrative_parser import UnpackingNarrativeParser
from ..ingestion.reference_resource_parser import ReferenceResourceParser
from ..ingestion.alignment_matrix_parser import AlignmentMatrixParser
from ..repositories.database import DatabaseManager
from ..utils.logging_config import get_logger


class FileValidationNode(Node):
    """Node for validating PDF files"""

    def __init__(self):
        super().__init__("FileValidation")
        self.logger = get_logger("file_validation_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Validate file path and return file information"""
        file_path = input_data.get("file_path", "")

        try:
            path = Path(file_path)

            # Convert to absolute path
            if not path.is_absolute():
                path = Path.cwd() / path

            # Check if file exists
            if not path.exists():
                raise ValueError(f"File not found: {path}")

            # Check if it's a file
            if not path.is_file():
                raise ValueError(f"Path is not a file: {path}")

            # Check file extension
            if path.suffix.lower() != ".pdf":
                raise ValueError(f"File must be a PDF: {path.suffix}")

            # Get file info
            file_size = path.stat().st_size

            return {
                "valid": True,
                "absolute_path": str(path.resolve()),
                "file_name": path.name,
                "file_size": file_size,
                "original_path": file_path,
            }

        except Exception as e:
            self.logger.error(f"File validation failed: {e}")
            return {"valid": False, "error": str(e), "original_path": file_path}


class DocumentClassificationNode(Node):
    """Node for classifying document types"""

    def __init__(self):
        super().__init__("DocumentClassification")
        self.classifier = DocumentClassifier()
        self.logger = get_logger("document_classification_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Classify document and return type information"""
        if not input_data.get("valid", False):
            raise ValueError(
                f"Invalid file: {input_data.get('error', 'Unknown error')}"
            )

        file_path = input_data["absolute_path"]

        try:
            # Classify document
            doc_type, confidence = self.classifier.classify(file_path)

            # Get recommended parser
            recommended_parser = self.classifier.get_recommended_parser(doc_type)

            return {
                **input_data,
                "document_type": doc_type,
                "confidence": confidence,
                "recommended_parser": recommended_parser,
                "classification_success": True,
            }

        except Exception as e:
            self.logger.error(f"Document classification failed: {e}")
            return {
                **input_data,
                "classification_success": False,
                "classification_error": str(e),
            }


class StandardsIngestionNode(Node):
    """Node for ingesting standards documents"""

    def __init__(
        self, db_manager: Optional[DatabaseManager] = None, use_vision: bool = False
    ):
        super().__init__("StandardsIngestion")
        self.db_manager = db_manager or DatabaseManager()
        self.use_vision = use_vision
        self.logger = get_logger("standards_ingestion_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Ingest standards document"""
        if not input_data.get("classification_success", False):
            raise ValueError(
                f"Classification failed: {input_data.get('classification_error', 'Unknown error')}"
            )

        file_path = input_data["absolute_path"]
        file_name = input_data["file_name"]
        file_id = input_data.get("file_id")

        try:
            # Initialize database
            self.db_manager.initialize_database()

            # Parse with standards parser
            parser = NCStandardsParser(use_vision=self.use_vision)
            parsed_standards = parser.parse_standards_document(file_path)

            # Convert to database models
            standards, objectives = parser.normalize_to_models(file_name)

            # Save to database
            self._save_to_database(standards, objectives, file_id)

            # Get statistics
            stats = parser.get_statistics()

            return {
                **input_data,
                "ingestion_success": True,
                "standards_count": len(standards),
                "objectives_count": len(objectives),
                "statistics": stats,
                "ingestion_type": "standards",
            }

        except Exception as e:
            self.logger.error(f"Standards ingestion failed: {e}")
            return {
                **input_data,
                "ingestion_success": False,
                "ingestion_error": str(e),
                "ingestion_type": "standards",
            }

    def _save_to_database(self, standards: List, objectives: List, file_id: Optional[str] = None) -> None:
        """Save standards and objectives to database with proper transaction management"""
        with self.db_manager.get_connection() as conn:
            try:
                # Start explicit transaction with immediate locking
                conn.execute("BEGIN IMMEDIATE")
                
                self.logger.info(f"Starting transaction to save {len(standards)} standards and {len(objectives)} objectives")
                
                # Save standards
                for standard in standards:
                    conn.execute(
                        """INSERT INTO standards
                           (standard_id, grade_level, strand_code, strand_name,
                            strand_description, standard_text, source_document, file_id,
                            ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            standard.standard_id,
                            standard.grade_level,
                            standard.strand_code,
                            standard.strand_name,
                            standard.strand_description,
                            standard.standard_text,
                            standard.source_document,
                            file_id,
                            standard.ingestion_date,
                            standard.version,
                        ),
                    )

                # Save objectives
                for objective in objectives:
                    conn.execute(
                        """INSERT INTO objectives (objective_id, standard_id, objective_text, file_id)
                           VALUES (?, ?, ?, ?)""",
                        (
                            objective.objective_id,
                            objective.standard_id,
                            objective.objective_text,
                            file_id,
                        ),
                    )

                # Commit the transaction
                conn.commit()
                self.logger.info(f"Successfully saved {len(standards)} standards and {len(objectives)} objectives to database")
                
            except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                # Rollback on any error
                conn.rollback()
                self.logger.error(f"Database transaction failed, rolled back: {e}")
                raise Exception(f"Failed to save standards and objectives to database: {str(e)}")


class UnpackingIngestionNode(Node):
    """Node for ingesting unpacking documents"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__("UnpackingIngestion")
        self.db_manager = db_manager or DatabaseManager()
        self.logger = get_logger("unpacking_ingestion_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Ingest unpacking document"""
        if not input_data.get("classification_success", False):
            raise ValueError(
                f"Classification failed: {input_data.get('classification_error', 'Unknown error')}"
            )

        file_path = input_data["absolute_path"]
        file_name = input_data["file_name"]
        file_id = input_data.get("file_id")

        try:
            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Parse with unpacking parser
            parser = UnpackingNarrativeParser()
            sections = parser.parse_unpacking_document(file_path)

            # Convert to database models
            unpacking_sections, teaching_strategies, assessment_guidance = (
                self._normalize_to_models(sections, file_name, file_id)
            )

            # Save to database
            self._save_to_database(
                unpacking_sections, teaching_strategies, assessment_guidance
            )

            # Get statistics
            stats = self._get_statistics(sections)

            return {
                **input_data,
                "ingestion_success": True,
                "sections_count": len(unpacking_sections),
                "strategies_count": len(teaching_strategies),
                "guidance_count": len(assessment_guidance),
                "statistics": stats,
                "ingestion_type": "unpacking",
            }

        except Exception as e:
            self.logger.error(f"Unpacking ingestion failed: {e}")
            return {
                **input_data,
                "ingestion_success": False,
                "ingestion_error": str(e),
                "ingestion_type": "unpacking",
            }

    def _ensure_extended_schema(self) -> None:
        """Ensure extended database schema exists"""
        from ..repositories.migrations import MigrationManager

        migrator = MigrationManager(str(self.db_manager.db_path))
        migrator.migrate_to_extended_schema()

    def _normalize_to_models(
        self, sections: List, file_name: str, file_id: Optional[str] = None
    ) -> Tuple[List, List, List]:
        """Convert parsed sections to database models"""
        from ..repositories.models_extended import (
            UnpackingSection,
            TeachingStrategy,
            AssessmentGuidance,
            generate_section_id,
            generate_strategy_id,
            generate_guidance_id,
        )
        from datetime import datetime

        ingestion_date = datetime.now().isoformat()

        unpacking_sections = []
        teaching_strategies = []
        assessment_guidance = []

        for section in sections:
            # Create content hash for unique ID generation
            import hashlib

            content_hash = hashlib.md5(section.content.encode()).hexdigest()[:8]

            # Create unpacking section
            section_id = generate_section_id(
                section.grade_level,
                section.section_title,
                section.page_number,
                content_hash,
            )
            unpacking_section = UnpackingSection(
                section_id=section_id,
                grade_level=section.grade_level,
                strand_code=section.strand_code,
                standard_id=section.standard_id,
                section_title=section.section_title,
                content=section.content,
                page_number=section.page_number,
                source_document=file_name,
                file_id=file_id,
                ingestion_date=ingestion_date,
            )
            unpacking_sections.append(unpacking_section)

            # Create teaching strategies
            for strategy_text in section.teaching_strategies:
                strategy_id = generate_strategy_id(section_id, strategy_text)
                strategy = TeachingStrategy(
                    strategy_id=strategy_id,
                    section_id=section_id,
                    strategy_text=strategy_text,
                    grade_level=section.grade_level,
                    strand_code=section.strand_code,
                    standard_id=section.standard_id,
                    source_document=file_name,
                    file_id=file_id,
                    page_number=section.page_number,
                    ingestion_date=ingestion_date,
                )
                teaching_strategies.append(strategy)

            # Create assessment guidance
            for guidance_text in section.assessment_guidance:
                guidance_id = generate_guidance_id(section_id, guidance_text)
                guidance = AssessmentGuidance(
                    guidance_id=guidance_id,
                    section_id=section_id,
                    guidance_text=guidance_text,
                    grade_level=section.grade_level,
                    strand_code=section.strand_code,
                    standard_id=section.standard_id,
                    source_document=file_name,
                    file_id=file_id,
                    page_number=section.page_number,
                    ingestion_date=ingestion_date,
                )
                assessment_guidance.append(guidance)

        return unpacking_sections, teaching_strategies, assessment_guidance

    def _save_to_database(
        self, sections: List, strategies: List, guidance: List
    ) -> None:
        """Save unpacking content to database with proper transaction management"""
        with self.db_manager.get_connection() as conn:
            try:
                # Start explicit transaction with immediate locking
                conn.execute("BEGIN IMMEDIATE")
                
                self.logger.info(f"Starting transaction to save {len(sections)} sections, {len(strategies)} strategies, and {len(guidance)} guidance items")
                
                # Save sections
                for section in sections:
                    conn.execute(
                        """INSERT INTO unpacking_sections
                           (section_id, grade_level, strand_code, standard_id,
                            section_title, content, page_number, source_document,
                            file_id, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            section.section_id,
                            section.grade_level,
                            section.strand_code,
                            section.standard_id,
                            section.section_title,
                            section.content,
                            section.page_number,
                            section.source_document,
                            section.file_id,
                            section.ingestion_date,
                            section.version,
                        ),
                    )

                # Save teaching strategies
                for strategy in strategies:
                    conn.execute(
                        """INSERT INTO teaching_strategies
                           (strategy_id, section_id, strategy_text, grade_level,
                            strand_code, standard_id, source_document, file_id, page_number, ingestion_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            strategy.strategy_id,
                            strategy.section_id,
                            strategy.strategy_text,
                            strategy.grade_level,
                            strategy.strand_code,
                            strategy.standard_id,
                            strategy.source_document,
                            strategy.file_id,
                            strategy.page_number,
                            strategy.ingestion_date,
                        ),
                    )

                # Save assessment guidance
                for guidance_item in guidance:
                    conn.execute(
                        """INSERT INTO assessment_guidance
                           (guidance_id, section_id, guidance_text, grade_level,
                            strand_code, standard_id, source_document, file_id, page_number, ingestion_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            guidance_item.guidance_id,
                            guidance_item.section_id,
                            guidance_item.guidance_text,
                            guidance_item.grade_level,
                            guidance_item.strand_code,
                            guidance_item.standard_id,
                            guidance_item.source_document,
                            guidance_item.file_id,
                            guidance_item.page_number,
                            guidance_item.ingestion_date,
                        ),
                    )

                # Commit the transaction
                conn.commit()
                self.logger.info(f"Successfully saved {len(sections)} sections, {len(strategies)} strategies, and {len(guidance)} guidance items to database")
                
            except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                # Rollback on any error
                conn.rollback()
                self.logger.error(f"Database transaction failed, rolled back: {e}")
                raise Exception(f"Failed to save unpacking content to database: {str(e)}")

    def _get_statistics(self, sections: List) -> Dict[str, Any]:
        """Get statistics about unpacking content"""
        grade_distribution = {}
        strand_distribution = {}
        total_strategies = 0
        total_guidance = 0

        for section in sections:
            # Count by grade
            grade = section.grade_level
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

            # Count by strand
            if section.strand_code:
                strand = section.strand_code
                strand_distribution[strand] = strand_distribution.get(strand, 0) + 1

            # Count strategies and guidance
            total_strategies += len(section.teaching_strategies)
            total_guidance += len(section.assessment_guidance)

        return {
            "total_sections": len(sections),
            "total_strategies": total_strategies,
            "total_guidance": total_guidance,
            "grade_distribution": grade_distribution,
            "strand_distribution": strand_distribution,
            "average_strategies_per_section": total_strategies / len(sections)
            if sections
            else 0,
            "average_guidance_per_section": total_guidance / len(sections)
            if sections
            else 0,
        }


class AlignmentIngestionNode(Node):
    """Node for ingesting alignment documents"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__("AlignmentIngestion")
        self.db_manager = db_manager or DatabaseManager()
        self.logger = get_logger("alignment_ingestion_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Ingest alignment document"""
        if not input_data.get("classification_success", False):
            raise ValueError(
                f"Classification failed: {input_data.get('classification_error', 'Unknown error')}"
            )

        file_path = input_data["absolute_path"]
        file_name = input_data["file_name"]
        file_id = input_data.get("file_id")

        try:
            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Parse with alignment parser
            parser = AlignmentMatrixParser()

            # Determine alignment type based on filename
            alignment_type = self._detect_alignment_type(file_name)
            relationships = parser.parse_alignment_document(file_path, alignment_type)

            # Convert to database models
            alignment_relationships, progression_mappings = self._normalize_to_models(
                relationships, file_name, file_id
            )

            # Save to database
            self._save_to_database(alignment_relationships, progression_mappings)

            # Get statistics
            stats = self._get_statistics(relationships)

            return {
                **input_data,
                "ingestion_success": True,
                "relationships_count": len(alignment_relationships),
                "mappings_count": len(progression_mappings),
                "statistics": stats,
                "ingestion_type": "alignment",
            }

        except Exception as e:
            self.logger.error(f"Alignment ingestion failed: {e}")
            return {
                **input_data,
                "ingestion_success": False,
                "ingestion_error": str(e),
                "ingestion_type": "alignment",
            }

    def _ensure_extended_schema(self) -> None:
        """Ensure extended database schema exists"""
        from backend.repositories.migrations_extended import MigrationManager

        migrator = MigrationManager(str(self.db_manager.db_path))
        migrator.migrate_to_extended_schema()

    def _detect_alignment_type(self, file_name: str) -> str:
        """Detect alignment type from filename"""
        file_name_lower = file_name.lower()

        if "horizontal" in file_name_lower:
            return "horizontal"
        elif "vertical" in file_name_lower:
            return "vertical"
        else:
            return "auto"  # Let parser decide

    def _normalize_to_models(
        self, relationships: List, file_name: str, file_id: Optional[str] = None
    ) -> Tuple[List, List]:
        """Convert parsed relationships to database models"""
        from backend.repositories.models_extended import (
            AlignmentRelationship,
            ProgressionMapping,
            generate_relationship_id,
            generate_mapping_id,
        )
        from datetime import datetime
        import json

        ingestion_date = datetime.now().isoformat()

        alignment_relationships = []
        progression_mappings = []

        for rel in relationships:
            if hasattr(rel, "standard_id"):  # AlignmentRelationship
                relationship_id = generate_relationship_id(
                    rel.standard_id, rel.related_standard_ids, rel.relationship_type
                )

                alignment_rel = AlignmentRelationship(
                    relationship_id=relationship_id,
                    standard_id=rel.standard_id,
                    related_standard_ids=rel.related_standard_ids,
                    relationship_type=rel.relationship_type,
                    grade_level=rel.grade_level,
                    strand_code=rel.strand_code,
                    description=rel.description,
                    source_document=file_name,
                    file_id=file_id,
                    page_number=rel.page_number,
                    ingestion_date=ingestion_date,
                )
                alignment_relationships.append(alignment_rel)

            elif hasattr(rel, "skill_name"):  # ProgressionMapping
                mapping_id = generate_mapping_id(rel.skill_name, rel.grade_levels)

                progression_map = ProgressionMapping(
                    mapping_id=mapping_id,
                    skill_name=rel.skill_name,
                    grade_levels=rel.grade_levels,
                    standard_mappings=rel.standard_mappings,
                    progression_notes=rel.progression_notes,
                    source_document=file_name,
                    file_id=file_id,
                    page_number=rel.page_number,
                    ingestion_date=ingestion_date,
                )
                progression_mappings.append(progression_map)

        return alignment_relationships, progression_mappings

    def _save_to_database(self, relationships: List, mappings: List) -> None:
        """Save alignment content to database with proper transaction management"""
        import json

        with self.db_manager.get_connection() as conn:
            try:
                # Start explicit transaction with immediate locking
                conn.execute("BEGIN IMMEDIATE")
                
                self.logger.info(f"Starting transaction to save {len(relationships)} relationships and {len(mappings)} mappings")
                
                # Save alignment relationships
                for rel in relationships:
                    conn.execute(
                        """INSERT INTO alignment_relationships
                           (relationship_id, standard_id, related_standard_ids,
                            relationship_type, grade_level, strand_code, description,
                            source_document, file_id, page_number, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            rel.relationship_id,
                            rel.standard_id,
                            json.dumps(rel.related_standard_ids),
                            rel.relationship_type,
                            rel.grade_level,
                            rel.strand_code,
                            rel.description,
                            rel.source_document,
                            rel.file_id,
                            rel.page_number,
                            rel.ingestion_date,
                            rel.version,
                        ),
                    )

                # Save progression mappings
                for mapping in mappings:
                    conn.execute(
                        """INSERT INTO progression_mappings
                           (mapping_id, skill_name, grade_levels, standard_mappings,
                            progression_notes, source_document, file_id, page_number, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            mapping.mapping_id,
                            mapping.skill_name,
                            json.dumps(mapping.grade_levels),
                            json.dumps(mapping.standard_mappings),
                            mapping.progression_notes,
                            mapping.source_document,
                            mapping.file_id,
                            mapping.page_number,
                            mapping.ingestion_date,
                            mapping.version,
                        ),
                    )
    
                # Commit the transaction
                conn.commit()
                self.logger.info(f"Successfully saved {len(relationships)} relationships and {len(mappings)} mappings to database")
                
            except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                # Rollback on any error
                conn.rollback()
                self.logger.error(f"Database transaction failed, rolled back: {e}")
                raise Exception(f"Failed to save alignment content to database: {str(e)}")

    def _get_statistics(self, relationships: List) -> Dict[str, Any]:
        """Get statistics about alignment content"""
        relationship_types = {}
        grade_distribution = {}
        strand_distribution = {}

        for rel in relationships:
            if hasattr(rel, "relationship_type"):  # AlignmentRelationship
                # Count by relationship type
                rel_type = rel.relationship_type
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

                # Count by grade
                grade = rel.grade_level
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

                # Count by strand
                strand = rel.strand_code
                strand_distribution[strand] = strand_distribution.get(strand, 0) + 1

        return {
            "total_relationships": len(
                [r for r in relationships if hasattr(r, "relationship_type")]
            ),
            "total_mappings": len(
                [r for r in relationships if hasattr(r, "skill_name")]
            ),
            "relationship_types": relationship_types,
            "grade_distribution": grade_distribution,
            "strand_distribution": strand_distribution,
        }


class ReferenceIngestionNode(Node):
    """Node for ingesting reference documents"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__("ReferenceIngestion")
        self.db_manager = db_manager or DatabaseManager()
        self.logger = get_logger("reference_ingestion_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Ingest reference document"""
        if not input_data.get("classification_success", False):
            raise ValueError(
                f"Classification failed: {input_data.get('classification_error', 'Unknown error')}"
            )

        file_path = input_data["absolute_path"]
        file_name = input_data["file_name"]
        file_id = input_data.get("file_id")

        try:
            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Parse with reference parser
            parser = ReferenceResourceParser()

            # Detect document type
            doc_type = self._detect_reference_type(file_name)
            entries = parser.parse_reference_document(file_path, doc_type)

            # Convert to database models
            glossary_entries, faq_entries, resource_entries = self._normalize_to_models(
                entries, file_name, file_id
            )

            # Save to database
            self._save_to_database(glossary_entries, faq_entries, resource_entries)

            # Get statistics
            stats = self._get_statistics(entries)

            return {
                **input_data,
                "ingestion_success": True,
                "glossary_count": len(glossary_entries),
                "faq_count": len(faq_entries),
                "resource_count": len(resource_entries),
                "statistics": stats,
                "ingestion_type": "reference",
            }

        except Exception as e:
            self.logger.error(f"Reference ingestion failed: {e}")
            return {
                **input_data,
                "ingestion_success": False,
                "ingestion_error": str(e),
                "ingestion_type": "reference",
            }

    def _ensure_extended_schema(self) -> None:
        """Ensure extended database schema exists"""
        from backend.repositories.migrations_extended import MigrationManager

        migrator = MigrationManager(str(self.db_manager.db_path))
        migrator.migrate_to_extended_schema()

    def _detect_reference_type(self, file_name: str) -> str:
        """Detect reference document type from filename"""
        file_name_lower = file_name.lower()

        if "glossary" in file_name_lower:
            return "glossary"
        elif "faq" in file_name_lower:
            return "faq"
        elif "catalog" in file_name_lower or "pd" in file_name_lower:
            return "catalog"
        elif "skills" in file_name_lower or "appendix" in file_name_lower:
            return "appendix"
        else:
            return "auto"  # Let parser decide

    def _normalize_to_models(
        self, entries: List, file_name: str, file_id: Optional[str] = None
    ) -> Tuple[List, List, List]:
        """Convert parsed entries to database models"""
        from backend.repositories.models_extended import (
            GlossaryEntry,
            FAQEntry,
            ResourceEntry,
            generate_glossary_id,
            generate_faq_id,
            generate_resource_id,
        )
        from datetime import datetime
        import json

        ingestion_date = datetime.now().isoformat()

        glossary_entries = []
        faq_entries = []
        resource_entries = []

        for entry in entries:
            if hasattr(entry, "term"):  # GlossaryEntry
                entry_id = generate_glossary_id(entry.term, entry.page_number)

                glossary_entry = GlossaryEntry(
                    entry_id=entry_id,
                    term=entry.term,
                    definition=entry.definition,
                    page_number=entry.page_number,
                    related_standards=entry.related_standards,
                    source_document=file_name,
                    file_id=file_id,
                    ingestion_date=ingestion_date,
                )
                glossary_entries.append(glossary_entry)

            elif hasattr(entry, "question"):  # FAQEntry
                entry_id = generate_faq_id(entry.question, entry.page_number)

                faq_entry = FAQEntry(
                    entry_id=entry_id,
                    question=entry.question,
                    answer=entry.answer,
                    page_number=entry.page_number,
                    category=entry.category,
                    source_document=file_name,
                    file_id=file_id,
                    ingestion_date=ingestion_date,
                )
                faq_entries.append(faq_entry)

            else:  # ResourceEntry
                entry_id = generate_resource_id(
                    entry.title, entry.content_type, entry.page_number
                )

                resource_entry = ResourceEntry(
                    entry_id=entry_id,
                    title=entry.title,
                    description=entry.description,
                    content_type=entry.content_type,
                    page_number=entry.page_number,
                    metadata=entry.metadata,
                    source_document=file_name,
                    file_id=file_id,
                    ingestion_date=ingestion_date,
                )
                resource_entries.append(resource_entry)

        return glossary_entries, faq_entries, resource_entries

    def _save_to_database(self, glossary: List, faq: List, resources: List) -> None:
        """Save reference content to database with proper transaction management"""
        import json

        with self.db_manager.get_connection() as conn:
            try:
                # Start explicit transaction with immediate locking
                conn.execute("BEGIN IMMEDIATE")
                
                self.logger.info(f"Starting transaction to save {len(glossary)} glossary entries, {len(faq)} FAQ entries, and {len(resources)} resource entries")
                
                # Save glossary entries
                for entry in glossary:
                    conn.execute(
                        """INSERT INTO glossary_entries
                           (entry_id, term, definition, page_number,
                            related_standards, source_document, file_id, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            entry.entry_id,
                            entry.term,
                            entry.definition,
                            entry.page_number,
                            json.dumps(entry.related_standards),
                            entry.source_document,
                            entry.file_id,
                            entry.ingestion_date,
                            entry.version,
                        ),
                    )

                # Save FAQ entries
                for entry in faq:
                    conn.execute(
                        """INSERT INTO faq_entries
                           (entry_id, question, answer, page_number,
                            category, source_document, file_id, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            entry.entry_id,
                            entry.question,
                            entry.answer,
                            entry.page_number,
                            entry.category,
                            entry.source_document,
                            entry.file_id,
                            entry.ingestion_date,
                            entry.version,
                        ),
                    )
    
                # Save resource entries
                for entry in resources:
                    conn.execute(
                        """INSERT INTO resource_entries
                           (entry_id, title, description, content_type,
                            page_number, metadata, source_document, file_id, ingestion_date, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            entry.entry_id,
                            entry.title,
                            entry.description,
                            entry.content_type,
                            entry.page_number,
                            json.dumps(entry.metadata),
                            entry.source_document,
                            entry.file_id,
                            entry.ingestion_date,
                            entry.version,
                        ),
                    )
    
                # Commit the transaction
                conn.commit()
                self.logger.info(f"Successfully saved {len(glossary)} glossary entries, {len(faq)} FAQ entries, and {len(resources)} resource entries to database")
                
            except (sqlite3.Error, sqlite3.DatabaseError, Exception) as e:
                # Rollback on any error
                conn.rollback()
                self.logger.error(f"Database transaction failed, rolled back: {e}")
                raise Exception(f"Failed to save reference content to database: {str(e)}")

    def _get_statistics(self, entries: List) -> Dict[str, Any]:
        """Get statistics about reference content"""
        content_types = {}
        categories = {}

        for entry in entries:
            if hasattr(entry, "content_type"):  # ResourceEntry
                content_type = entry.content_type
                content_types[content_type] = content_types.get(content_type, 0) + 1

            elif hasattr(entry, "category"):  # FAQEntry
                category = entry.category or "uncategorized"
                categories[category] = categories.get(category, 0) + 1

        return {
            "total_glossary": len([e for e in entries if hasattr(e, "term")]),
            "total_faq": len([e for e in entries if hasattr(e, "question")]),
            "total_resources": len([e for e in entries if hasattr(e, "content_type")]),
            "content_types": content_types,
            "categories": categories,
        }


class IngestionRouterNode(Node):
    """Node that routes to appropriate ingestion processor based on document type"""

    def __init__(self):
        super().__init__("IngestionRouter")
        self.logger = get_logger("ingestion_router_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Route to appropriate ingestion node"""
        if not input_data.get("classification_success", False):
            raise ValueError(
                f"Classification failed: {input_data.get('classification_error', 'Unknown error')}"
            )

        doc_type = input_data["document_type"]

        # Add routing information
        return {**input_data, "route_to": self._get_route_target(doc_type)}

    def _get_route_target(self, doc_type: DocumentType) -> str:
        """Get the target node for the document type"""
        routing_map = {
            DocumentType.STANDARDS: "StandardsIngestion",
            DocumentType.UNPACKING: "UnpackingIngestion",
            DocumentType.ALIGNMENT: "AlignmentIngestion",
            DocumentType.GUIDE: "ReferenceIngestion",
            DocumentType.GLOSSARY: "ReferenceIngestion",
            DocumentType.UNKNOWN: "StandardsIngestion",  # Default fallback
        }

        return routing_map.get(doc_type, "StandardsIngestion")


class IngestionSummaryNode(Node):
    """Node for generating ingestion summary"""

    def __init__(self):
        super().__init__("IngestionSummary")
        self.logger = get_logger("ingestion_summary_node")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Generate summary of ingestion results"""
        success = input_data.get("ingestion_success", False)
        ingestion_type = input_data.get("ingestion_type", "unknown")

        summary = {
            "file_name": input_data.get("file_name", ""),
            "document_type": input_data.get("document_type", "unknown"),
            "confidence": input_data.get("confidence", 0.0),
            "ingestion_type": ingestion_type,
            "success": success,
        }

        if success:
            summary.update(
                {
                    "standards_count": input_data.get("standards_count", 0),
                    "objectives_count": input_data.get("objectives_count", 0),
                    "statistics": input_data.get("statistics", {}),
                }
            )
        else:
            summary["error"] = input_data.get("ingestion_error", "Unknown error")

        return {**input_data, "summary": summary}
