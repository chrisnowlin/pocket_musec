"""Ingest commands for pocket_musec"""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import logging

from backend.ingestion.nc_standards_unified_parser import (
    NCStandardsParser,
    ParsingStrategy,
)
from backend.ingestion.document_classifier import DocumentClassifier, DocumentType
from backend.repositories.database import DatabaseManager
from backend.utils.error_handling import (
    handle_keyboard_interrupts,
    handle_file_errors,
    recovery_manager,
)
from backend.utils.logging_config import get_logger
from backend.utils.progress import ProgressTracker

ingest_app = typer.Typer(help="Ingest standards and other data")
console = Console()
logger = get_logger("ingest_command")


@ingest_app.command()
@handle_keyboard_interrupts
@handle_file_errors
def standards(
    pdf_path: str = typer.Argument(..., help="Path to the NC Music Standards PDF file"),
    db_path: str | None = typer.Option(
        None,
        "--db-path",
        help="Custom path to the SQLite database (uses default if not provided)",
    ),
    force: bool = typer.Option(
        False, "--force", help="Force re-ingestion even if standards already exist"
    ),
    use_vision: bool = typer.Option(
        True,
        "--use-vision/--no-vision",
        help="Use vision AI processing (more accurate, ~10 min/document). Use --no-vision for fast hybrid mode.",
    ),
):
    """Ingest North Carolina music standards from PDF"""

    logger.info(
        "Starting standards ingestion",
        context={
            "pdf_path": pdf_path,
            "db_path": db_path,
            "force": force,
            "use_vision": use_vision,
        },
    )

    with logger.log_performance("standards_ingestion"):
        try:
            # Validate PDF path
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                error_msg = f"PDF file not found: {pdf_path}"
                logger.error(error_msg)
                console.print(f"[red]Error: {error_msg}[/red]")
                raise typer.Exit(1)

            logger.info(
                "PDF file validated", context={"file_size": pdf_file.stat().st_size}
            )

            # Initialize database
            console.print("🔧 Initializing database...")
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()
            logger.info("Database initialized")

            # Check if standards already exist
            if _has_standards(db_manager):
                if not force:
                    console.print(
                        "[yellow]Standards already exist in database. Use --force to re-ingest.[/yellow]"
                    )
                    logger.info("Standards already exist, skipping ingestion")
                    return
                else:
                    console.print(
                        "[yellow]Clearing existing standards (--force specified)...[/yellow]"
                    )
                    _clear_standards(db_manager)
                    logger.info("Existing standards cleared")

            # Parse PDF with progress tracking
            if use_vision:
                console.print(
                    f"📄 Parsing PDF with vision AI: {pdf_path} (this may take ~10 min)"
                )
            else:
                console.print(f"📄 Parsing PDF: {pdf_path}")

            with logger.log_performance("pdf_parsing"):
                strategy = (
                    ParsingStrategy.VISION_FIRST
                    if use_vision
                    else ParsingStrategy.TABLE_BASED
                )
                parser = NCStandardsParser(strategy=strategy)
                parsed_standards = parser.parse_standards_document(str(pdf_file))

                logger.info(
                    "PDF parsed successfully",
                    context={
                        "parsed_standards_count": len(parsed_standards)
                        if parsed_standards
                        else 0
                    },
                )

            # Convert to database models
            console.print("🔄 Converting to database format...")
            with logger.log_performance("model_conversion"):
                standards, objectives = parser.normalize_to_models(pdf_file.name)

                logger.info(
                    "Models converted successfully",
                    context={
                        "standards_count": len(standards) if standards else 0,
                        "objectives_count": len(objectives) if objectives else 0,
                    },
                )

            # Save to database
            console.print("💾 Saving to database...")
            with logger.log_performance("database_save"):
                _save_standards(db_manager, standards, objectives)
                logger.info("Data saved to database")

            # Show statistics
            stats = parser.get_statistics()
            console.print("\n[green]✅ Ingestion completed successfully![/green]")
            console.print(f"\n📊 Statistics:")
            console.print(f"  • Total standards: {stats.get('total_standards', 0)}")
            console.print(f"  • Total objectives: {stats.get('total_objectives', 0)}")
            console.print(
                f"  • Average objectives per standard: {stats.get('average_objectives_per_standard', 0):.1f}"
            )

            if stats.get("grade_distribution"):
                console.print(f"\n📚 Grade distribution:")
                for grade, count in stats["grade_distribution"].items():
                    console.print(f"  • {grade}: {count} standards")

            if stats.get("strand_distribution"):
                console.print(f"\n🎵 Strand distribution:")
                for strand, count in stats["strand_distribution"].items():
                    strand_name = parser.strand_mappings.get(strand, (strand, ""))[0]
                    console.print(f"  • {strand_name} ({strand}): {count} standards")

            logger.info("Standards ingestion completed successfully", context=stats)

        except Exception as e:
            logger.error(
                "Standards ingestion failed",
                error=e,
                context={"pdf_path": pdf_path, "db_path": db_path},
            )
            recovery_manager.log_error(e, {"operation": "standards_ingestion"})
            console.print(f"[red]Error during ingestion: {e}[/red]")
            raise typer.Exit(1)


def _has_standards(db_manager: DatabaseManager) -> bool:
    """Check if standards already exist in database"""
    try:
        with db_manager.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM standards").fetchone()
            return result[0] > 0
    except Exception:
        return False


def _clear_standards(db_manager: DatabaseManager):
    """Clear all standards and objectives from database"""
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM objectives")
        conn.execute("DELETE FROM standards")
        conn.commit()


def ingest_standards(pdf_path: str, db_path: str | None = None, force: bool = False):
    """Wrapper function for ingesting standards from CLI"""
    return standards(pdf_path, db_path, force)


@ingest_app.command()
@handle_keyboard_interrupts
@handle_file_errors
def auto(
    pdf_path: str = typer.Argument(
        ..., help="Path to NC Music Education PDF file (any type)"
    ),
    db_path: str | None = typer.Option(
        None,
        "--db-path",
        help="Custom path to the SQLite database (uses default if not provided)",
    ),
    force: bool = typer.Option(
        False, "--force", help="Force re-ingestion even if data already exists"
    ),
    use_vision: bool = typer.Option(
        False,
        "--use-vision/--no-vision",
        help="Use vision AI processing for standards documents (slower but more accurate)",
    ),
):
    """Auto-detect document type and ingest with appropriate parser"""

    logger.info(
        "Starting auto ingestion with document classification",
        context={"pdf_path": pdf_path, "db_path": db_path, "force": force},
    )

    with logger.log_performance("auto_ingestion"):
        try:
            # Validate PDF path
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                error_msg = f"PDF file not found: {pdf_path}"
                logger.error(error_msg)
                console.print(f"[red]Error: {error_msg}[/red]")
                raise typer.Exit(1)

            # Classify document
            console.print("🔍 Analyzing document type...")
            classifier = DocumentClassifier()
            doc_type, confidence = classifier.classify(str(pdf_file))

            console.print(
                f"📄 Document type: [cyan]{doc_type.value}[/cyan] (confidence: {confidence:.0%})"
            )

            # Route to appropriate handler
            if doc_type == DocumentType.STANDARDS:
                console.print("→ Using standards parser (table-based extraction)\n")
                _ingest_standards_document(pdf_file, db_path, force, use_vision)

            elif doc_type == DocumentType.UNPACKING:
                console.print("→ Using unpacking parser (narrative extraction)\n")
                console.print(
                    "[yellow]⚠️  Unpacking document ingestion coming soon![/yellow]"
                )
                console.print(
                    "   These documents contain valuable supplementary content:"
                )
                console.print("   • Glossary terms")
                console.print("   • Teaching suggestions")
                console.print("   • Essential questions")
                console.print("   • Vertical alignment notes")
                logger.info("Unpacking parser not yet implemented")
                return

            elif doc_type == DocumentType.ALIGNMENT:
                console.print(
                    "[yellow]ℹ️  Alignment documents are informational[/yellow]"
                )
                console.print(
                    "   These documents show skill progression across grades."
                )
                console.print("   No ingestion needed - use for reference.")
                return

            elif doc_type == DocumentType.GUIDE:
                console.print("[yellow]ℹ️  Guide documents are informational[/yellow]")
                console.print("   These documents provide implementation guidance.")
                console.print("   No ingestion needed - use for reference.")
                return

            else:
                console.print(f"[yellow]⚠️  Unknown document type[/yellow]")
                console.print("   Falling back to standards parser...")
                _ingest_standards_document(pdf_file, db_path, force, use_vision)

        except Exception as e:
            logger.error(
                "Auto ingestion failed",
                error=e,
                context={"pdf_path": pdf_path, "db_path": db_path},
            )
            recovery_manager.log_error(e, {"operation": "auto_ingestion"})
            console.print(f"[red]Error during ingestion: {e}[/red]")
            raise typer.Exit(1)


def _ingest_standards_document(
    pdf_file: Path, db_path: str | None, force: bool, use_vision: bool
):
    """Helper to ingest standards document (extracted from standards command)"""

    # Initialize database
    console.print("🔧 Initializing database...")
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    logger.info("Database initialized")

    # Check if standards already exist
    if _has_standards(db_manager):
        if not force:
            console.print(
                "[yellow]Standards already exist in database. Use --force to re-ingest.[/yellow]"
            )
            logger.info("Standards already exist, skipping ingestion")
            return
        else:
            console.print(
                "[yellow]Clearing existing standards (--force specified)...[/yellow]"
            )
            _clear_standards(db_manager)
            logger.info("Existing standards cleared")

    # Parse PDF with progress tracking
    if use_vision:
        console.print(
            f"📄 Parsing PDF with vision AI: {pdf_file.name} (this may take ~10 min)"
        )
    else:
        console.print(f"📄 Parsing PDF: {pdf_file.name}")

    with logger.log_performance("pdf_parsing"):
        strategy = (
            ParsingStrategy.VISION_FIRST if use_vision else ParsingStrategy.TABLE_BASED
        )
        parser = NCStandardsParser(strategy=strategy)
        parsed_standards = parser.parse_standards_document(str(pdf_file))

        logger.info(
            "PDF parsed successfully",
            context={
                "parsed_standards_count": len(parsed_standards)
                if parsed_standards
                else 0
            },
        )

    # Convert to database models
    console.print("🔄 Converting to database format...")
    with logger.log_performance("model_conversion"):
        standards, objectives = parser.normalize_to_models(pdf_file.name)

        logger.info(
            "Models converted successfully",
            context={
                "standards_count": len(standards) if standards else 0,
                "objectives_count": len(objectives) if objectives else 0,
            },
        )

    # Save to database
    console.print("💾 Saving to database...")
    with logger.log_performance("database_save"):
        _save_standards(db_manager, standards, objectives)
        logger.info("Data saved to database")

    # Show statistics
    stats = parser.get_statistics()
    console.print("\n[green]✅ Ingestion completed successfully![/green]")
    console.print(f"\n📊 Statistics:")
    console.print(f"  • Total standards: {stats.get('total_standards', 0)}")
    console.print(f"  • Total objectives: {stats.get('total_objectives', 0)}")
    console.print(
        f"  • Average objectives per standard: {stats.get('average_objectives_per_standard', 0):.1f}"
    )

    if stats.get("grade_distribution"):
        console.print(f"\n📚 Grade distribution:")
        for grade, count in stats["grade_distribution"].items():
            console.print(f"  • {grade}: {count} standards")

    if stats.get("strand_distribution"):
        console.print(f"\n🎵 Strand distribution:")
        for strand, count in stats["strand_distribution"].items():
            strand_name = parser.strand_mappings.get(strand, (strand, ""))[0]
            console.print(f"  • {strand_name} ({strand}): {count} standards")

    logger.info("Standards ingestion completed successfully", context=stats)


def _save_standards(db_manager: DatabaseManager, standards, objectives):
    """Save standards and objectives to database"""
    with db_manager.get_connection() as conn:
        # Save standards
        for standard in standards:
            conn.execute(
                """INSERT INTO standards 
                   (standard_id, grade_level, strand_code, strand_name, 
                    strand_description, standard_text, source_document, 
                    ingestion_date, version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                ),
            )

        # Save objectives
        for objective in objectives:
            conn.execute(
                """INSERT INTO objectives (objective_id, standard_id, objective_text)
                   VALUES (?, ?, ?)""",
                (
                    objective.objective_id,
                    objective.standard_id,
                    objective.objective_text,
                ),
            )

        conn.commit()
