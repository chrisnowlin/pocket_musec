"""CLI command for generating embeddings for standards"""

import typer
import logging
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from backend.llm.embeddings import StandardsEmbedder

app = typer.Typer(help="Generate embeddings for standards and objectives")
console = Console()

logger = logging.getLogger(__name__)


@app.command()
def generate(
    force: bool = typer.Option(False, "--force", "-f", help="Regenerate all embeddings, even if they exist"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Number of standards to process in each batch"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging")
):
    """Generate embeddings for all standards and objectives"""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    console.print(Panel.fit(
        "[bold blue]Generating Embeddings for Standards[/bold blue]\n\n"
        "This will create semantic embeddings for all standards and objectives\n"
        "to enable intelligent search and recommendations.",
        title="Embeddings Generation"
    ))
    
    try:
        embedder = StandardsEmbedder()
        
        # Check current stats
        stats = embedder.embeddings_manager.get_embedding_stats()
        
        if stats["standard_embeddings"] > 0 and not force:
            console.print(f"[yellow]Found {stats['standard_embeddings']} existing standard embeddings[/yellow]")
            console.print(f"[yellow]Found {stats['objective_embeddings']} existing objective embeddings[/yellow]")
            
            if not typer.confirm("Do you want to regenerate all embeddings? Use --force to skip this prompt."):
                console.print("[green]Embedding generation cancelled.[/green]")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Generating embeddings...", total=100)
            
            # Generate embeddings
            result_stats = embedder.embed_all_standards(batch_size=batch_size)
            
            progress.update(task, completed=100)
        
        # Display results
        console.print("\n[bold green]✅ Embedding generation complete![/bold green]\n")
        
        table = Table(title="Embedding Generation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Successfully embedded", str(result_stats["success"]))
        table.add_row("Failed to embed", str(result_stats["failed"]))
        table.add_row("Skipped (already exists)", str(result_stats["skipped"]))
        
        console.print(table)
        
        # Show final stats
        final_stats = embedder.embeddings_manager.get_embedding_stats()
        console.print(f"\n[blue]Database now contains:[/blue]")
        console.print(f"  • {final_stats['standard_embeddings']} standard embeddings")
        console.print(f"  • {final_stats['objective_embeddings']} objective embeddings")
        console.print(f"  • Embedding dimension: {final_stats['embedding_dimension']}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error generating embeddings: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def stats():
    """Show statistics about embeddings in the database"""
    
    try:
        embedder = StandardsEmbedder()
        stats = embedder.embeddings_manager.get_embedding_stats()
        
        console.print(Panel.fit(
            "[bold blue]Embeddings Statistics[/bold blue]",
            title="Database Status"
        ))
        
        table = Table(title="Current Embeddings")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Standard embeddings", str(stats["standard_embeddings"]))
        table.add_row("Objective embeddings", str(stats["objective_embeddings"]))
        table.add_row("Embedding dimension", str(stats["embedding_dimension"]))
        
        console.print(table)
        
        if stats["standard_embeddings"] == 0:
            console.print("\n[yellow]No embeddings found. Run 'pocketflow embeddings generate' to create them.[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error getting stats: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    grade_level: Optional[str] = typer.Option(None, "--grade", "-g", help="Filter by grade level"),
    strand: Optional[str] = typer.Option(None, "--strand", "-s", help="Filter by strand code"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Minimum similarity threshold")
):
    """Search for standards using semantic similarity"""
    
    try:
        embedder = StandardsEmbedder()
        
        console.print(f"[bold blue]Searching for standards similar to:[/bold blue] '{query}'")
        
        if grade_level or strand:
            filters = []
            if grade_level:
                filters.append(f"grade: {grade_level}")
            if strand:
                filters.append(f"strand: {strand}")
            console.print(f"[dim]Filters: {', '.join(filters)}[/dim]")
        
        # Generate embedding for query
        query_embedding = embedder.embeddings_manager.embed_query(query)
        
        # Search for similar standards
        results = embedder.embeddings_manager.search_similar_standards(
            query_embedding=query_embedding,
            grade_level=grade_level,
            strand_code=strand,
            limit=limit,
            similarity_threshold=threshold
        )
        
        if not results:
            console.print(f"[yellow]No standards found matching '{query}' with threshold {threshold}[/yellow]")
            return
        
        console.print(f"\n[bold green]Found {len(results)} matching standards:[/bold green]\n")
        
        table = Table(title="Semantic Search Results")
        table.add_column("Similarity", style="cyan", width=10)
        table.add_column("Grade", style="magenta", width=12)
        table.add_column("Strand", style="green", width=8)
        table.add_column("Standard ID", style="yellow", width=15)
        table.add_column("Standard Text", style="white", width=50)
        
        for embedded_standard, similarity in results:
            table.add_row(
                f"{similarity:.3f}",
                embedded_standard.grade_level,
                embedded_standard.strand_code,
                embedded_standard.standard_id,
                embedded_standard.standard_text[:80] + "..." if len(embedded_standard.standard_text) > 80 else embedded_standard.standard_text
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error searching standards: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def clear():
    """Clear all embeddings from the database"""
    
    console.print("[bold red]⚠️  This will delete all embeddings from the database![/bold red]")
    
    if not typer.confirm("Are you sure you want to delete all embeddings?"):
        console.print("[green]Operation cancelled.[/green]")
        return
    
    try:
        embedder = StandardsEmbedder()
        embedder.embeddings_manager.delete_all_embeddings()
        
        console.print("[bold green]✅ All embeddings deleted from database[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error clearing embeddings: {str(e)}[/bold red]")
        raise typer.Exit(1)


def generate_embeddings(force: bool = False, batch_size: int = 10, verbose: bool = False):
    """Wrapper function for test compatibility"""
    return generate(force=force, batch_size=batch_size, verbose=verbose)


if __name__ == "__main__":
    app()