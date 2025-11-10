# PocketMusec CLI Commands Documentation

## Overview

PocketMusec is an AI-powered lesson planning assistant for music teachers. The CLI provides three main command groups: `ingest`, `generate`, and `embeddings`.

## Installation & Setup

```bash
# Install dependencies
uv install

# Run the CLI
uv run python main.py --help
```

## Main Commands

### `pocketflow` - Root Command

```bash
pocketflow --help
```

**Subcommands:**
- `ingest` - Ingest standards and other data
- `generate` - Generate lesson plans and content  
- `embeddings` - Manage embeddings for standards
- `version` - Show version information

---

## 1. Ingest Commands (`pocketflow ingest`)

### `ingest standards` - Import NC Music Standards

Import North Carolina music education standards from PDF documents into the SQLite database.

```bash
pocketflow ingest standards <PDF_PATH> [OPTIONS]
```

**Arguments:**
- `<PDF_PATH>` (required) - Path to the NC Music Standards PDF file

**Options:**
- `--db-path <PATH>` - Custom path to SQLite database (uses default if not provided)
- `--force` - Force re-ingestion even if standards already exist

**Examples:**
```bash
# Basic ingestion
pocketflow ingest standards "NC Music Standards.pdf"

# Custom database location
pocketflow ingest standards "NC Music Standards.pdf" --db-path "/custom/path/standards.db"

# Force re-ingestion (overwrites existing data)
pocketflow ingest standards "NC Music Standards.pdf" --force
```

**Output:**
- Progress indicators for PDF parsing
- Statistics on standards and objectives ingested
- Grade and strand distribution breakdown
- Success/failure status

**Requirements:**
- PDF file must exist and be readable
- Sufficient disk space for database
- PDF should contain NC music standards format

---

## 2. Generate Commands (`pocketflow generate`)

### `generate lesson` - Interactive Lesson Generation

Generate music lesson plans through an interactive conversational interface.

```bash
pocketflow generate lesson [OPTIONS]
```

**Options:**
- `--interactive/--no-interactive` - Run in interactive mode (default: interactive)
- `--output <FILENAME>, -o <FILENAME>` - Save lesson directly to file

**Examples:**
```bash
# Start interactive lesson generation
pocketflow generate lesson

# Save directly to file without interactive prompts
pocketflow generate lesson --output "my_lesson.md"

# Non-interactive mode (not yet implemented)
pocketflow generate lesson --no-interactive
```

**Interactive Workflow:**

1. **Welcome Screen** - Introduction and overview
2. **Grade Selection** - Choose from K-12 grade levels
3. **Strand Selection** - Select from four music strands:
   - CN (Creating Music)
   - CR (Critical Response)
   - PR (Performing Music) 
   - RE (Responding to Music)
4. **Standard Selection** - Choose specific standard or describe topic
5. **Objective Refinement** - Select learning objectives
6. **Context Collection** - Add additional context (optional)
7. **Lesson Generation** - AI generates complete lesson plan
8. **Review & Edit** - View, edit, and save the lesson

**Navigation Commands:**
- `quit`, `exit`, `q` - Exit lesson generation
- `back` - Go to previous step (where supported)
- `help` - Show available options

**Editor Integration:**
- Automatically detects system default editor
- Creates temporary file with lesson content
- Tracks changes and maintains draft history
- Supports multiple edit cycles

**Output Features:**
- Structured lesson plan with standards alignment
- Learning objectives and assessment suggestions
- Differentiation strategies
- Draft history tracking
- Session summary with timestamps

---

## 3. Embeddings Commands (`pocketflow embeddings`)

### `embeddings generate` - Create Semantic Embeddings

Generate vector embeddings for standards and objectives to enable intelligent search and recommendations.

```bash
pocketflow embeddings generate [OPTIONS]
```

**Options:**
- `--force, -f` - Regenerate all embeddings, even if they exist
- `--batch-size <NUMBER>, -b <NUMBER>` - Batch size for processing (default: 10)
- `--verbose, -v` - Show detailed logging

**Examples:**
```bash
# Generate embeddings (checks for existing)
pocketflow embeddings generate

# Force regeneration of all embeddings
pocketflow embeddings generate --force

# Custom batch size for performance tuning
pocketflow embeddings generate --batch-size 20

# Verbose output for debugging
pocketflow embeddings generate --verbose
```

**Process:**
1. Checks for existing embeddings
2. Processes standards in batches
3. Creates vector representations using AI models
4. Stores embeddings in database for fast retrieval
5. Shows progress and statistics

### `embeddings stats` - View Embedding Statistics

Display current status of embeddings in the database.

```bash
pocketflow embeddings stats
```

**Output:**
- Number of standard embeddings
- Number of objective embeddings
- Embedding dimension
- Database status

### `embeddings search` - Semantic Search

Search for standards using natural language queries and semantic similarity.

```bash
pocketflow embeddings search <QUERY> [OPTIONS]
```

**Arguments:**
- `<QUERY>` (required) - Natural language search query

**Options:**
- `--grade <GRADE>, -g <GRADE>` - Filter by grade level
- `--strand <CODE>, -s <CODE>` - Filter by strand code (CN, CR, PR, RE)
- `--limit <NUMBER>, -l <NUMBER>` - Maximum results (default: 10)
- `--threshold <FLOAT>, -t <FLOAT>` - Minimum similarity threshold (default: 0.5)

**Examples:**
```bash
# Basic semantic search
pocketflow embeddings search "rhythm activities for kindergarten"

# Filter by grade level
pocketflow embeddings search "music composition" --grade "8th Grade"

# Filter by strand
pocketflow embeddings search "performance assessment" --strand "PR"

# Adjust similarity threshold
pocketflow embeddings search "music theory" --threshold 0.7

# Limit results
pocketflow embeddings search "ensemble techniques" --limit 5
```

**Output:**
- Similarity scores for each match
- Grade level and strand information
- Standard ID and truncated text
- Ranked by relevance

### `embeddings clear` - Remove All Embeddings

Delete all embeddings from the database (use with caution).

```bash
pocketflow embeddings clear
```

**Warning:** This operation cannot be undone. You'll need to regenerate embeddings afterward.

---

## 4. Utility Commands

### `version` - Show Version Information

Display the current PocketMusec version.

```bash
pocketflow version
```

**Output:**
```
pocketflow v0.1.0
```

---

## Configuration

### Environment Variables

Set these in your environment or `.env` file:

```bash
# Chutes API Configuration
CHUTES_API_KEY=your_api_key_here
CHUTES_BASE_URL=https://api.chutes.ai

# Database Configuration (optional)
DATABASE_PATH=./data/standards.db

# Logging Configuration
LOG_LEVEL=INFO
```

### Default File Locations

- **Database:** `./data/standards.db` (created automatically)
- **Temporary Files:** System temp directory (cleaned automatically)
- **Log Files:** Console output (configurable)

---

## Error Handling

### Common Issues and Solutions

**1. PDF Parsing Errors**
```
Error: PDF file not found: /path/to/file.pdf
```
- Verify the PDF path is correct
- Ensure PDF is not password protected
- Check file permissions

**2. Database Connection Issues**
```
Error: unable to open database file
```
- Ensure data directory exists
- Check disk space
- Verify write permissions

**3. API Connection Errors**
```
Error: Failed to connect to Chutes API
```
- Verify CHUTES_API_KEY is set
- Check internet connection
- Confirm API service status

**4. Editor Launch Failures**
```
Error: Failed to launch editor
```
- Set EDITOR environment variable
- Install a text editor (nano, vim, code)
- Check editor installation

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# For embeddings generation
pocketflow embeddings generate --verbose

# Set environment variable
export LOG_LEVEL=DEBUG
pocketflow generate lesson
```

---

## Performance Tips

### Large PDF Processing
- Use `--batch-size` to tune memory usage
- Monitor disk space during ingestion
- Consider splitting large PDFs

### Embedding Generation
- Batch size of 10-20 works well for most systems
- Use `--force` only when necessary
- Monitor API rate limits

### Database Optimization
- SQLite automatically optimizes queries
- Indexes created for grade/strand searches
- Consider periodic database cleanup

---

## Integration Examples

### Shell Scripts

**Batch lesson generation:**
```bash
#!/bin/bash
for grade in "Kindergarten" "1st Grade" "2nd Grade"; do
    echo "Generating lesson for $grade..."
    pocketflow generate lesson --output "${grade}_lesson.md"
done
```

**Automated ingestion workflow:**
```bash
#!/bin/bash
# Ingest standards
pocketflow ingest standards "NC Standards.pdf" --force

# Generate embeddings
pocketflow embeddings generate --force

# Show statistics
pocketflow embeddings stats
```

### Python Integration

```python
import subprocess
import json

def generate_lesson(grade_level, output_file):
    """Generate lesson using CLI from Python"""
    cmd = [
        "pocketflow", "generate", "lesson",
        "--output", output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

# Usage
success = generate_lesson("3rd Grade", "grade3_lesson.md")
```

---

## Support

### Getting Help
- Use `--help` flag on any command
- Check the project documentation
- Review error messages carefully

### Reporting Issues
Include the following in bug reports:
- Command used and full output
- Operating system and Python version
- PDF file information (if applicable)
- Environment variables (sanitized)

### Feature Requests
Submit feature requests through the project's issue tracker with:
- Use case description
- Expected behavior
- Implementation suggestions (optional)