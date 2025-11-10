"""Ingest commands for pocket_musec"""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import logging

from backend.ingestion.standards_parser import NCStandardsParser
from backend.repositories.database import DatabaseManager
from backend.utils.error_handling import handle_keyboard_interrupts, handle_file_errors, recovery_manager
from backend.utils.logging_config import get_logger
from backend.utils.progress import ProgressTracker

ingest_app = typer.Typer(help="Ingest standards and other data")
console = Console()
logger = get_logger("ingest_command")


@ingest_app.command()
@handle_keyboard_interrupts
@handle_file_errors
def standards(
    pdf_path: str = typer.Argument(
        ...,
        help="Path to the NC Music Standards PDF file"
    ),
    db_path: str = typer.Option(
        None,
        "--db-path",
        help="Custom path to the SQLite database (uses default if not provided)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force re-ingestion even if standards already exist"
    )
):
    """Ingest North Carolina music standards from PDF"""
    
    logger.info("Starting standards ingestion", context={
        'pdf_path': pdf_path,
        'db_path': db_path,
        'force': force
    })
    
    with logger.log_performance("standards_ingestion"):
        try:
            # Validate PDF path
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                error_msg = f"PDF file not found: {pdf_path}"
                logger.error(error_msg)
                console.print(f"[red]Error: {error_msg}[/red]")
                raise typer.Exit(1)
            
            logger.info("PDF file validated", context={'file_size': pdf_file.stat().st_size})
            
            # Initialize database
            console.print("🔧 Initializing database...")
            db_manager = DatabaseManager(db_path)
            db_manager.initialize_database()
            logger.info("Database initialized")
            
            # Check if standards already exist
            if not force and _has_standards(db_manager):
                console.print("[yellow]Standards already exist in database. Use --force to re-ingest.[/yellow]")
                logger.info("Standards already exist, skipping ingestion")
                return
            
            # Parse PDF with progress tracking
            console.print(f"📄 Parsing PDF: {pdf_path}")
            progress_tracker = ProgressTracker.get_pdf_processing_tracker()
            
            with progress_tracker:
                parser = NCStandardsParser()
                parsed_standards = parser.parse_standards_document(str(pdf_file))
                
                logger.info("PDF parsed successfully", context={
                    'parsed_standards_count': len(parsed_standards) if parsed_standards else 0
                })
            
            # Convert to database models
            console.print("🔄 Converting to database format...")
            with logger.log_performance("model_conversion"):
                standards, objectives = parser.normalize_to_models(pdf_file.name)
                
                logger.info("Models converted successfully", context={
                    'standards_count': len(standards) if standards else 0,
                    'objectives_count': len(objectives) if objectives else 0
                })
            
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
            console.print(f"  • Average objectives per standard: {stats.get('average_objectives_per_standard', 0):.1f}")
            
            if stats.get('grade_distribution'):
                console.print(f"\n📚 Grade distribution:")
                for grade, count in stats['grade_distribution'].items():
                    console.print(f"  • {grade}: {count} standards")
            
            if stats.get('strand_distribution'):
                console.print(f"\n🎵 Strand distribution:")
                for strand, count in stats['strand_distribution'].items():
                    strand_name = parser.strand_mappings.get(strand, (strand, ""))[0]
                    console.print(f"  • {strand_name} ({strand}): {count} standards")
            
            logger.info("Standards ingestion completed successfully", context=stats)
            
        except Exception as e:
            logger.error("Standards ingestion failed", error=e, context={
                'pdf_path': pdf_path,
                'db_path': db_path
            })
            recovery_manager.log_error(e, {'operation': 'standards_ingestion'})
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


def ingest_standards(pdf_path: str, db_path: str = None, force: bool = False):
    """Wrapper function for ingesting standards from CLI"""
    return standards(pdf_path, db_path, force)


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
                    standard.version
                )
            )
        
        # Save objectives
        for objective in objectives:
            conn.execute(
                """INSERT INTO objectives (objective_id, standard_id, objective_text)
                   VALUES (?, ?, ?)""",
                (objective.objective_id, objective.standard_id, objective.objective_text)
            )
        
        conn.commit()