"""Main CLI application for pocket_musec"""

import typer
from rich.console import Console

app = typer.Typer(
    name="pocketflow",
    help="AI-powered lesson planning assistant for music teachers",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version():
    """Show version information"""
    console.print("pocketflow v0.1.0")


@app.command()
def ingest():
    """Ingest standards and other data"""
    console.print("Use 'pocketflow ingest standards' to ingest NC music standards")


@app.command()
def generate():
    """Generate lesson plans and content"""
    console.print("Use 'pocketflow generate lesson' to generate lesson plans")


@app.command()
def embeddings():
    """Manage embeddings for standards and objectives"""
    console.print("Use 'pocketflow embeddings generate' to create embeddings")
    console.print("Use 'pocketflow embeddings search' to search standards")
    console.print("Use 'pocketflow embeddings stats' to view statistics")


# Add subcommands
from .commands.ingest import ingest_app
from .commands.generate import generate_app
from .commands.embed import app as embed_app

app.add_typer(ingest_app, name="ingest", help="Ingest standards and other data")
app.add_typer(generate_app, name="generate", help="Generate lesson plans and content")
app.add_typer(embed_app, name="embeddings", help="Manage embeddings for standards")


if __name__ == "__main__":
    app()