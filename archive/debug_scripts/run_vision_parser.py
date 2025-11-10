#!/usr/bin/env python3
"""Run vision parser on NC Music Standards documents"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.ingestion.standards_parser_vision import NCStandardsParser
from backend.repositories.database import DatabaseManager
from backend.utils.logging_config import get_logger

def main():
    """Main function to run vision parser on standards documents"""
    
    logger = get_logger("vision_parser_runner")
    console = logger.console
    
    console.print("[bold blue]🎵 PocketMusec Vision Parser[/bold blue]")
    console.print("Processing NC Music Standards with AI vision enhancement...\n")
    
    # Find standards PDFs
    standards_dir = Path("NC Music Standards and Resources")
    if not standards_dir.exists():
        console.print(f"[red]Error: Standards directory not found: {standards_dir}[/red]")
        return
    
    pdf_files = list(standards_dir.glob("*.pdf"))
    if not pdf_files:
        console.print("[red]No PDF files found in standards directory[/red]")
        return
    
    console.print(f"[green]Found {len(pdf_files)} PDF files to process[/green]")
    for pdf in pdf_files:
        console.print(f"  • {pdf.name}")
    
    console.print("\n[yellow]This will take some time as each page is processed with AI vision...[/yellow]")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Initialize vision parser
    parser = NCStandardsParser(use_vision=True)
    
    total_standards = 0
    total_objectives = 0
    processing_times = []
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        console.print(f"\n[bold cyan]Processing {i}/{len(pdf_files)}: {pdf_file.name}[/bold cyan]")
        
        start_time = time.time()
        
        try:
            console.print(f"[yellow]Processing {pdf_file.name} with vision AI...[/yellow]")
                # Parse with vision enhancement
                standards = parser.parse_standards_document(str(pdf_file))
                
                # Convert to database models
                db_standards, db_objectives = parser.normalize_to_models(pdf_file.name)
                
                # Save to database
                with db_manager.get_connection() as conn:
                    # Clear existing data for this document
                    conn.execute("DELETE FROM standards WHERE source_document = ?", (pdf_file.name,))
                    conn.execute("DELETE FROM objectives WHERE standard_id IN (SELECT standard_id FROM standards WHERE source_document = ?)", (pdf_file.name,))
                    
                    # Insert new data
                    for standard in db_standards:
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
                    
                    for objective in db_objectives:
                        conn.execute(
                            """INSERT INTO objectives (objective_id, standard_id, objective_text)
                               VALUES (?, ?, ?)""",
                            (objective.objective_id, objective.standard_id, objective.objective_text)
                        )
                    
                    conn.commit()
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
                # Get statistics
                stats = parser.get_statistics()
                
                console.print(f"[green]✅ Completed {pdf_file.name}[/green]")
                console.print(f"  • Standards: {stats.get('total_standards', 0)}")
                console.print(f"  • Objectives: {stats.get('total_objectives', 0)}")
                console.print(f"  • Processing time: {processing_time:.1f}s")
                console.print(f"  • Vision enhanced: {stats.get('vision_enhanced', False)}")
                
                total_standards += stats.get('total_standards', 0)
                total_objectives += stats.get('total_objectives', 0)
                
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}", error=e)
            console.print(f"[red]❌ Failed to process {pdf_file.name}: {e}[/red]")
            continue
    
    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold green]🎉 Vision Processing Complete![/bold green]")
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  • Files processed: {len(pdf_files)}")
    console.print(f"  • Total standards extracted: {total_standards}")
    console.print(f"  • Total objectives extracted: {total_objectives}")
    console.print(f"  • Average processing time: {sum(processing_times)/len(processing_times):.1f}s per file")
    console.print(f"  • Total processing time: {sum(processing_times):.1f}s")
    
    # Database verification
    with db_manager.get_connection() as conn:
        std_count = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]
        obj_count = conn.execute("SELECT COUNT(*) FROM objectives").fetchone()[0]
        
        console.print(f"\n[bold]Database Verification:[/bold]")
        console.print(f"  • Standards in database: {std_count}")
        console.print(f"  • Objectives in database: {obj_count}")
        
        if std_count == total_standards and obj_count == total_objectives:
            console.print("[green]✅ Database counts match extraction totals[/green]")
        else:
            console.print("[yellow]⚠️  Database counts don't match extraction totals[/yellow]")
    
    console.print("\n[blue]Vision-enhanced standards are now ready for lesson generation![/blue]")
    console.print("="*60)

if __name__ == "__main__":
    main()