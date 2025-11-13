"""Ingestion Agent for PocketFlow framework - Handles document ingestion through conversation"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import os

from .agent import Agent
from .flow import Flow
from .store import Store
from ..ingestion.document_classifier import DocumentClassifier, DocumentType
from ..ingestion.nc_standards_unified_parser import NCStandardsParser, ParsingStrategy
from ..ingestion.unpacking_narrative_parser import UnpackingNarrativeParser
from ..ingestion.reference_resource_parser import ReferenceResourceParser
from ..ingestion.alignment_matrix_parser import AlignmentMatrixParser
from ..repositories.database import DatabaseManager
from ..utils.error_handling import handle_file_errors
from ..utils.logging_config import get_logger


class IngestionAgent(Agent):
    """Agent for ingesting music education documents through conversation"""

    def __init__(
        self,
        flow: Flow,
        store: Store,
        db_manager: Optional[DatabaseManager] = None,
        document_classifier: Optional[DocumentClassifier] = None,
    ):
        super().__init__(flow, store, "IngestionAgent")
        self.db_manager = db_manager or DatabaseManager()
        self.document_classifier = document_classifier or DocumentClassifier()
        self.logger = get_logger("ingestion_agent")

        # Initialize ingestion state
        self.ingestion_context: Dict[str, Any] = {}

        # Set up state handlers
        self._setup_state_handlers()

        # Start with welcome state
        self.set_state("welcome")

    def _setup_state_handlers(self) -> None:
        """Set up handlers for each conversation state"""
        self.add_state_handler("welcome", self._handle_welcome)
        self.add_state_handler("file_path", self._handle_file_path)
        # Document classification is handled internally, not as a separate state
        self.add_state_handler("ingestion_options", self._handle_ingestion_options)
        self.add_state_handler("advanced_options", self._handle_advanced_options)
        self.add_state_handler("processing", self._handle_processing)
        self.add_state_handler("complete", self._handle_complete)

    def _show_welcome_message(self) -> str:
        """Show welcome message without changing state"""
        response = (
            "📄 Welcome to PocketMusec Document Ingestion!\n\n"
            "I can help you ingest various music education documents:\n"
            "• NC Music Standards (formal documents)\n"
            "• Grade-level Unpacking documents\n"
            "• Alignment matrices (horizontal/vertical)\n"
            "• Reference materials (glossaries, FAQs)\n"
            "• Implementation guides\n\n"
            "Please provide the path to the PDF document you'd like to ingest, "
            "or type 'quit' to exit."
        )

        return response

    def _handle_welcome(self, message: str) -> str:
        """Handle welcome state and file path collection"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Document ingestion cancelled. Goodbye!"

        # Show welcome message and move to file path collection
        response = self._show_welcome_message()
        self.set_state("file_path")

        return response

    def _handle_file_path(self, message: str) -> str:
        """Handle file path validation and document classification"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Document ingestion cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("welcome")
            return self._show_welcome_message()

        file_path = message.strip()

        # Validate file path
        validation_result = self._validate_file_path(file_path)
        if not validation_result["valid"]:
            return f"❌ {validation_result['error']}\n\nPlease provide a valid PDF file path or type 'back' to return."

        # Store file path and classify document
        self.ingestion_context["file_path"] = validation_result["absolute_path"]
        self.ingestion_context["file_name"] = Path(
            validation_result["absolute_path"]
        ).name

        # Classify document
        self.set_state("document_classification")
        return self._classify_document()

    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """Validate file path and return normalized result"""
        try:
            path = Path(file_path)

            # Convert to absolute path
            if not path.is_absolute():
                path = Path.cwd() / path

            # Check if file exists
            if not path.exists():
                return {"valid": False, "error": f"File not found: {path}"}

            # Check if it's a file
            if not path.is_file():
                return {"valid": False, "error": f"Path is not a file: {path}"}

            # Check file extension
            if path.suffix.lower() != ".pdf":
                return {"valid": False, "error": f"File must be a PDF: {path.suffix}"}

            # Check file size (warn if very large)
            file_size = path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                self.logger.warning(
                    f"Large file detected: {file_size / (1024 * 1024):.1f}MB"
                )

            return {
                "valid": True,
                "absolute_path": str(path.resolve()),
                "file_size": file_size,
            }

        except Exception as e:
            return {"valid": False, "error": f"Invalid path: {str(e)}"}

    def _classify_document(self) -> str:
        """Classify the document and show results"""
        try:
            file_path = self.ingestion_context["file_path"]
            file_name = self.ingestion_context["file_name"]

            # Classify document
            doc_type, confidence = self.document_classifier.classify(file_path)

            # Store classification results
            self.ingestion_context["document_type"] = doc_type
            self.ingestion_context["confidence"] = confidence

            # Get recommended parser
            recommended_parser = self.document_classifier.get_recommended_parser(
                doc_type
            )
            self.ingestion_context["recommended_parser"] = recommended_parser

            # Show classification results
            response = (
                f"🔍 Document Analysis Complete\n\n"
                f"File: {file_name}\n"
                f"Type: {doc_type.value}\n"
                f"Confidence: {confidence:.0%}\n"
                f"Recommended parser: {recommended_parser}\n\n"
            )

            # Show type-specific information
            response += self._get_document_type_info(doc_type)

            response += (
                "Would you like to proceed with ingestion? "
                "Type 'yes' to continue, 'no' to choose a different file, "
                "or 'options' to see advanced options."
            )

            self.set_state("ingestion_options")
            return response

        except Exception as e:
            self.logger.error(f"Document classification failed: {e}")
            return (
                f"❌ Error classifying document: {str(e)}\n\n"
                "Please try a different file or type 'back' to return."
            )

    def _get_document_type_info(self, doc_type: DocumentType) -> str:
        """Get specific information about the document type"""
        info_map = {
            DocumentType.STANDARDS: (
                "📋 This appears to be a formal standards document.\n"
                "I'll extract standards, objectives, and store them in the database.\n"
            ),
            DocumentType.UNPACKING: (
                "📚 This appears to be an unpacking document.\n"
                "I'll extract narrative content, teaching strategies, and guidance.\n"
                "Note: Unpacking ingestion is coming soon!\n"
            ),
            DocumentType.ALIGNMENT: (
                "🔗 This appears to be an alignment document.\n"
                "I'll extract relationships between standards across grade levels.\n"
            ),
            DocumentType.GUIDE: (
                "📖 This appears to be a guide document.\n"
                "These are typically reference materials that don't require ingestion.\n"
            ),
            DocumentType.GLOSSARY: (
                "📝 This appears to be a glossary or reference document.\n"
                "I'll extract definitions and reference materials.\n"
            ),
            DocumentType.UNKNOWN: (
                "❓ I couldn't confidently classify this document.\n"
                "I'll try to process it as a standards document.\n"
            ),
        }

        return info_map.get(doc_type, info_map[DocumentType.UNKNOWN])

    def _handle_ingestion_options(self, message: str) -> str:
        """Handle ingestion confirmation and options"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Document ingestion cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("file_path")
            return "Please provide a new PDF file path, or type 'back' again to return to welcome."

        if message.lower() in ["no", "n"]:
            # Start over with new file
            self.ingestion_context.clear()
            self.set_state("file_path")
            return "Please provide a new PDF file path, or type 'back' to return to welcome."

        if message.lower() in ["options", "settings", "advanced"]:
            self.set_state("advanced_options")
            return self._show_advanced_options()

        if message.lower() in ["yes", "y", "proceed", "continue"]:
            return self._start_ingestion()

        return (
            "Please type 'yes' to proceed with ingestion, 'no' to choose a different file, "
            "or 'options' to see advanced settings."
        )

    def _handle_advanced_options(self, message: str) -> str:
        """Handle advanced options state"""
        if message.lower() in ["quit", "exit", "q"]:
            self.set_state("complete")
            return "Document ingestion cancelled. Goodbye!"

        if message.lower() in ["back", "b"]:
            self.set_state("ingestion_options")
            return self._get_ingestion_confirmation()

        # Handle specific option selections
        if message.isdigit() and message in ["1", "2", "3", "4"]:
            return self._process_advanced_option(message)

        return "Please select an option number (1-4), or type 'back' to return to ingestion options."

    def _get_ingestion_confirmation(self) -> str:
        """Get the ingestion confirmation message"""
        doc_type = self.ingestion_context.get("document_type", DocumentType.UNKNOWN)
        file_name = self.ingestion_context.get("file_name", "Unknown file")
        confidence = self.ingestion_context.get("confidence", 0.0)
        recommended_parser = self.ingestion_context.get("recommended_parser", "unknown")

        response = (
            f"🔍 Document Analysis Complete\n\n"
            f"File: {file_name}\n"
            f"Type: {doc_type.value}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Recommended parser: {recommended_parser}\n\n"
        )

        response += self._get_document_type_info(doc_type)
        response += (
            "Would you like to proceed with ingestion? "
            "Type 'yes' to continue, 'no' to choose a different file, "
            "or 'options' to see advanced options."
        )

        return response

    def _process_advanced_option(self, option: str) -> str:
        """Process selected advanced option"""
        doc_type = self.ingestion_context.get("document_type", DocumentType.UNKNOWN)

        # For now, just acknowledge the option and return to confirmation
        option_descriptions = {
            "1": "Vision AI processing",
            "2": "Fast table-based processing",
            "3": "Force re-ingestion",
            "4": "Preview extraction results",
        }

        if doc_type == DocumentType.UNPACKING:
            option_descriptions = {
                "1": "Teaching strategies only",
                "2": "Assessment examples only",
                "3": "All content sections",
            }
        elif doc_type == DocumentType.ALIGNMENT:
            option_descriptions = {
                "1": "Horizontal relationships only",
                "2": "Vertical progressions only",
                "3": "All alignment data",
            }
        elif doc_type in [DocumentType.GLOSSARY, DocumentType.GUIDE]:
            option_descriptions = {
                "1": "Glossary terms only",
                "2": "FAQ entries only",
                "3": "All reference content",
            }

        selected = option_descriptions.get(option, f"Option {option}")

        # Store the option in context
        self.ingestion_context["advanced_option"] = selected

        return (
            f"✅ Selected: {selected}\n\n"
            "Type 'yes' to proceed with this option, 'back' to change it, "
            "or 'options' to see all choices again."
        )

    def _show_advanced_options(self) -> str:
        """Show advanced ingestion options"""
        doc_type = self.ingestion_context.get("document_type", DocumentType.UNKNOWN)

        response = "⚙️ Advanced Ingestion Options\n\n"

        if doc_type == DocumentType.STANDARDS:
            response += (
                "1. Use vision AI processing (slower but more accurate)\n"
                "2. Use fast table-based processing\n"
                "3. Force re-ingestion (overwrite existing data)\n"
                "4. Preview extraction results\n"
            )
        elif doc_type == DocumentType.UNPACKING:
            response += (
                "1. Extract teaching strategies only\n"
                "2. Extract assessment examples only\n"
                "3. Extract all content sections\n"
            )
        elif doc_type == DocumentType.ALIGNMENT:
            response += (
                "1. Extract horizontal relationships only\n"
                "2. Extract vertical progressions only\n"
                "3. Extract all alignment data\n"
            )
        elif doc_type in [DocumentType.GLOSSARY, DocumentType.GUIDE]:
            response += (
                "1. Extract glossary terms only\n"
                "2. Extract FAQ entries only\n"
                "3. Extract all reference content\n"
            )
        else:
            response += (
                "1. Extract all available content\n"
                "2. Preview extraction results\n"
                "3. Dry run (validate without saving)\n"
            )

        response += "\nType an option number or 'back' to return."
        return response

    def _start_ingestion(self) -> str:
        """Start the document ingestion process"""
        self.set_state("processing")

        doc_type = self.ingestion_context["document_type"]
        file_path = self.ingestion_context["file_path"]

        try:
            # Initialize database
            self.db_manager.initialize_database()

            # Route to appropriate ingestion method
            if doc_type == DocumentType.STANDARDS:
                return self._ingest_standards_document(file_path)
            elif doc_type == DocumentType.UNPACKING:
                return self._ingest_unpacking_document(file_path)
            elif doc_type == DocumentType.ALIGNMENT:
                return self._ingest_alignment_document(file_path)
            elif doc_type in [DocumentType.GLOSSARY, DocumentType.GUIDE]:
                return self._ingest_reference_document(file_path)
            else:
                # Fallback to standards processing
                return self._ingest_standards_document(file_path)

        except Exception as e:
            self.logger.error(f"Ingestion failed: {e}")
            return (
                f"❌ Ingestion failed: {str(e)}\n\n"
                "Please check the file and try again, or type 'back' to choose a different file."
            )

    def _ingest_standards_document(self, file_path: str) -> str:
        """Ingest a standards document"""
        try:
            # Parse with standards parser
            parser = NCStandardsParser(use_vision=False)  # Default to fast mode
            parsed_standards = parser.parse_standards_document(file_path)

            # Convert to database models
            standards, objectives = parser.normalize_to_models(Path(file_path).name)

            # Save to database
            self._save_standards_to_database(standards, objectives)

            # Generate embeddings for the ingested standards
            try:
                file_id = self.ingestion_context.get("file_id")
                if file_id:
                    from backend.llm.embeddings import StandardsEmbedder
                    embedder = StandardsEmbedder()
                    embedding_stats = embedder.embed_standards_from_file(file_id)
                    logger.info(f"Generated embeddings for file {file_id}: {embedding_stats}")
                    
                    # Store embedding results in context
                    self.ingestion_context["embedding_results"] = embedding_stats
            except Exception as e:
                logger.warning(f"Failed to generate embeddings for ingested standards: {e}")

            # Get statistics
            stats = parser.get_statistics()

            # Store results
            self.ingestion_context["ingestion_results"] = {
                "standards_count": len(standards),
                "objectives_count": len(objectives),
                "statistics": stats,
            }

            self.set_state("complete")

            return (
                "✅ Standards Ingestion Complete!\n\n"
                f"📊 Results:\n"
                f"• Standards processed: {len(standards)}\n"
                f"• Objectives processed: {len(objectives)}\n"
                f"• Average objectives per standard: {stats.get('average_objectives_per_standard', 0):.1f}\n\n"
                "The data has been saved to the database and is ready for use in lesson generation.\n\n"
                "Type 'new' to ingest another document or 'quit' to exit."
            )

        except Exception as e:
            self.logger.error(f"Standards ingestion failed: {e}")
            raise

    def _ingest_unpacking_document(self, file_path: str) -> str:
        """Ingest an unpacking document"""
        try:
            from backend.pocketflow.ingestion_nodes import UnpackingIngestionNode

            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Create and run unpacking ingestion node
            ingestion_node = UnpackingIngestionNode(self.db_manager)

            # Prepare input data
            input_data = {
                "absolute_path": file_path,
                "file_name": Path(file_path).name,
                "file_id": self.ingestion_context.get("file_id"),
                "classification_success": True,
                "document_type": DocumentType.UNPACKING,
            }

            # Process ingestion
            result = ingestion_node.process(input_data)

            if result.get("ingestion_success", False):
                # Store results
                self.ingestion_context["ingestion_results"] = {
                    "sections_count": result.get("sections_count", 0),
                    "strategies_count": result.get("strategies_count", 0),
                    "guidance_count": result.get("guidance_count", 0),
                    "statistics": result.get("statistics", {}),
                }

                self.set_state("complete")

                return (
                    "✅ Unpacking Document Ingestion Complete!\n\n"
                    f"📊 Results:\n"
                    f"• Sections processed: {result.get('sections_count', 0)}\n"
                    f"• Teaching strategies: {result.get('strategies_count', 0)}\n"
                    f"• Assessment guidance: {result.get('guidance_count', 0)}\n\n"
                    "The unpacking content has been saved to the database and is ready for use.\n\n"
                    "Type 'new' to ingest another document or 'quit' to exit."
                )
            else:
                error = result.get("ingestion_error", "Unknown error")
                return f"❌ Unpacking ingestion failed: {error}\n\nType 'back' to try again."

        except Exception as e:
            self.logger.error(f"Unpacking ingestion failed: {e}")
            return (
                f"❌ Unpacking ingestion failed: {str(e)}\n\n"
                "Please check the file and try again, or type 'back' to choose a different file."
            )

    def _ingest_alignment_document(self, file_path: str) -> str:
        """Ingest an alignment document"""
        try:
            from backend.pocketflow.ingestion_nodes import AlignmentIngestionNode

            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Create and run alignment ingestion node
            ingestion_node = AlignmentIngestionNode(self.db_manager)

            # Prepare input data
            input_data = {
                "absolute_path": file_path,
                "file_name": Path(file_path).name,
                "file_id": self.ingestion_context.get("file_id"),
                "classification_success": True,
                "document_type": DocumentType.ALIGNMENT,
            }

            # Process ingestion
            result = ingestion_node.process(input_data)

            if result.get("ingestion_success", False):
                # Store results
                self.ingestion_context["ingestion_results"] = {
                    "relationships_count": result.get("relationships_count", 0),
                    "mappings_count": result.get("mappings_count", 0),
                    "statistics": result.get("statistics", {}),
                }

                self.set_state("complete")

                return (
                    "✅ Alignment Document Ingestion Complete!\n\n"
                    f"📊 Results:\n"
                    f"• Relationships processed: {result.get('relationships_count', 0)}\n"
                    f"• Progression mappings: {result.get('mappings_count', 0)}\n\n"
                    "The alignment data has been saved to the database and is ready for use.\n\n"
                    "Type 'new' to ingest another document or 'quit' to exit."
                )
            else:
                error = result.get("ingestion_error", "Unknown error")
                return f"❌ Alignment ingestion failed: {error}\n\nType 'back' to try again."

        except Exception as e:
            self.logger.error(f"Alignment ingestion failed: {e}")
            return (
                f"❌ Alignment ingestion failed: {str(e)}\n\n"
                "Please check the file and try again, or type 'back' to choose a different file."
            )

    def _ingest_reference_document(self, file_path: str) -> str:
        """Ingest a reference document"""
        try:
            from backend.pocketflow.ingestion_nodes import ReferenceIngestionNode

            # Initialize database with extended schema
            self._ensure_extended_schema()

            # Create and run reference ingestion node
            ingestion_node = ReferenceIngestionNode(self.db_manager)

            # Prepare input data
            input_data = {
                "absolute_path": file_path,
                "file_name": Path(file_path).name,
                "file_id": self.ingestion_context.get("file_id"),
                "classification_success": True,
                "document_type": DocumentType.GLOSSARY,  # or GUIDE
            }

            # Process ingestion
            result = ingestion_node.process(input_data)

            if result.get("ingestion_success", False):
                # Store results
                self.ingestion_context["ingestion_results"] = {
                    "glossary_count": result.get("glossary_count", 0),
                    "faq_count": result.get("faq_count", 0),
                    "resource_count": result.get("resource_count", 0),
                    "statistics": result.get("statistics", {}),
                }

                self.set_state("complete")

                return (
                    "✅ Reference Document Ingestion Complete!\n\n"
                    f"📊 Results:\n"
                    f"• Glossary entries: {result.get('glossary_count', 0)}\n"
                    f"• FAQ entries: {result.get('faq_count', 0)}\n"
                    f"• Resource entries: {result.get('resource_count', 0)}\n\n"
                    "The reference content has been saved to the database and is ready for use.\n\n"
                    "Type 'new' to ingest another document or 'quit' to exit."
                )
            else:
                error = result.get("ingestion_error", "Unknown error")
                return f"❌ Reference ingestion failed: {error}\n\nType 'back' to try again."

        except Exception as e:
            self.logger.error(f"Reference ingestion failed: {e}")
            return (
                f"❌ Reference ingestion failed: {str(e)}\n\n"
                "Please check the file and try again, or type 'back' to choose a different file."
            )

    def _save_standards_to_database(self, standards: List, objectives: List) -> None:
        """Save standards and objectives to database"""
        with self.db_manager.get_connection() as conn:
            # Clear existing standards if needed
            # conn.execute("DELETE FROM objectives")
            # conn.execute("DELETE FROM standards")

            # Get file_id from ingestion context
            file_id = self.ingestion_context.get("file_id")

            # Save standards
            for standard in standards:
                conn.execute(
                    """INSERT INTO standards
                       (standard_id, grade_level, strand_code, strand_name,
                        strand_description, standard_text, source_document,
                        ingestion_date, version, file_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        standard.standard_id,
                        standard.grade_level,
                        standard.strand_code,
                        standard.strand_name,
                        standard.strand_description,
                        standard.standard_text,
                        standard.source_document,
                        standard.ingestion_date,
                        standard.version,
                        file_id,
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

            conn.commit()

    def _handle_processing(self, message: str) -> str:
        """Handle processing state (should not be reached in normal flow)"""
        return "Processing is already underway. Please wait..."

    def _handle_complete(self, message: str) -> str:
        """Handle completion state"""
        if message.lower() in ["new", "another", "restart"]:
            # Start over with new document
            self.ingestion_context.clear()
            self.set_state("welcome")
            return self._show_welcome_message()

        if message.lower() in ["quit", "exit", "q"]:
            return "Document ingestion complete. Goodbye!"

        return "Ingestion complete! Type 'new' to ingest another document or 'quit' to exit."

    def get_ingestion_context(self) -> Dict[str, Any]:
        """Get the current ingestion context"""
        return self.ingestion_context.copy()

    def get_ingestion_results(self) -> Optional[Dict[str, Any]]:
        """Get the results of the last ingestion"""
        return self.ingestion_context.get("ingestion_results")

    def _ensure_extended_schema(self) -> None:
        """Ensure extended database schema exists"""
        from backend.repositories.migrations import MigrationManager

        migrator = MigrationManager(str(self.db_manager.db_path))
        migrator.migrate_to_extended_schema()

    def reset_ingestion(self) -> None:
        """Reset the ingestion context for a new document"""
        self.ingestion_context.clear()
        self.clear_history()
        self.set_state("welcome")
