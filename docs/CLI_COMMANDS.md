# PocketMusec CLI Commands Documentation

## ⚠️ DEPRECATED - CLI Removed

**Important Notice:** The CLI interface has been completely removed from PocketMusec as of version 0.4.0. All functionality is now available through the modern web interface at `http://localhost:5173`.

### Migration Information

For complete migration details, see:
- **[CLI Removal Complete](CLI_REMOVAL_COMPLETE.md)** - Full migration documentation
- **[User Guide](USER_GUIDE.md)** - Web interface documentation
- **[Teacher Guide](TEACHER_GUIDE.md)** - Educational usage guide

### Feature Parity

All CLI functionality has been migrated to the web interface:

| CLI Command | Web Interface Location |
|-------------|-----------------------|
| `pocketmusec ingest standards` | Available through web interface setup |
| `pocketmusec generate lesson` | Web interface → "New Lesson" |
| `pocketmusec embeddings generate` | Web interface → "Embeddings" → "Generate" |
| `pocketmusec embeddings stats` | Web interface → "Embeddings" → "Statistics" |
| `pocketmusec embeddings search` | Web interface → "Embeddings" → "Search" |
| `pocketmusec embeddings clear` | Web interface → "Embeddings" → "Batch" |

---

## Historical Documentation

The following documentation is preserved for historical reference only. **The CLI is no longer supported.**

### Overview

PocketMusec was an AI-powered lesson planning assistant for music teachers. The CLI provided three main command groups: `ingest`, `generate`, and `embeddings`.

## Installation & Setup

```bash
# Install dependencies
uv install

# Run the CLI
uv run python main.py --help
```

## Main Commands

### `pocketmusec` - Root Command

```bash
pocketmusec --help
```

**Subcommands:**
- `ingest` - Ingest standards and other data
- `generate` - Generate lesson plans and content  
- `embeddings` - Manage embeddings for standards
- `version` - Show version information

---

## 1. Ingest Commands (`pocketflow ingest`)

### `ingest standards` - Import NC Music Standards

Import North Carolina music education standards from PDF documents into SQLite database.

```bash
pocketmusec ingest standards <PDF_PATH> [OPTIONS]
```

**Arguments:**
- `<PDF_PATH>` (required) - Path to the NC Music Standards PDF file

**Options:**
- `--db-path <PATH>` - Custom path to SQLite database (uses default if not provided)
- `--force` - Force re-ingestion even if standards already exist

**Examples:**
```bash
# Basic ingestion
pocketmusec ingest standards "NC Music Standards.pdf"

# Custom database location
pocketmusec ingest standards "NC Music Standards.pdf" --db-path "/custom/path/pocket_musec.db"

# Force re-ingestion (overwrites existing data)
pocketmusec ingest standards "NC Music Standards.pdf" --force
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
pocketmusec generate lesson [OPTIONS]
```

**Options:**
- `--interactive/--no-interactive` - Run in interactive mode (default: interactive)
- `--output <FILENAME>, -o <FILENAME>` - Save lesson directly to file

**Examples:**
```bash
# Start interactive lesson generation
pocketmusec generate lesson

# Save directly to file without interactive prompts
pocketmusec generate lesson --output "my_lesson.md"

# Non-interactive mode (not yet implemented)
pocketmusec generate lesson --no-interactive
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
pocketmusec embeddings generate [OPTIONS]
```

**Options:**
- `--force, -f` - Regenerate all embeddings, even if they exist
- `--batch-size <NUMBER>, -b <NUMBER>` - Batch size for processing (default: 10)
- `--verbose, -v` - Show detailed logging

**Examples:**
```bash
# Generate embeddings (checks for existing)
pocketmusec embeddings generate

# Force regeneration of all embeddings
pocketmusec embeddings generate --force

# Custom batch size for performance tuning
pocketmusec embeddings generate --batch-size 20

# Verbose output for debugging
pocketmusec embeddings generate --verbose
```

**Process:**
1. Checks for existing embeddings
2. Processes standards in batches
3. Creates vector representations using AI models
4. Stores embeddings in database for fast retrieval
5. Saves prepared texts to `data/prepared_texts/` for inspection and tweaking
6. Shows progress and statistics

### `embeddings stats` - View Embedding Statistics

Display current status of embeddings in the database.

```bash
pocketmusec embeddings stats
```

**Output:**
- Number of standard embeddings
- Number of objective embeddings
- Embedding dimension
- Database status

### `embeddings search` - Semantic Search

Search for standards using natural language queries and semantic similarity.

```bash
pocketmusec embeddings search <QUERY> [OPTIONS]
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
pocketmusec embeddings search "rhythm activities for kindergarten"

# Filter by grade level
pocketmusec embeddings search "music composition" --grade "8th Grade"

# Filter by strand
pocketmusec embeddings search "performance assessment" --strand "PR"

# Adjust similarity threshold
pocketmusec embeddings search "music theory" --threshold 0.7

# Limit results
pocketmusec embeddings search "ensemble techniques" --limit 5
```

**Output:**
- Similarity scores for each match
- Grade level and strand information
- Standard ID and truncated text
- Ranked by relevance

### `embeddings clear` - Remove All Embeddings

Delete all embeddings from the database (use with caution).

```bash
pocketmusec embeddings clear
```

**Warning:** This operation cannot be undone. You'll need to regenerate embeddings afterward.

### `embeddings texts` - List Prepared Text Files

Display all prepared text files that were saved during embedding generation.

```bash
pocketmusec embeddings texts
```

**Output:**
- Count of standard and objective prepared texts
- List of IDs with prepared texts
- File location information

### `embeddings show-text` - View Prepared Text

Show the exact text that was sent to the embedding API for a specific standard or objective.

```bash
pocketmusec embeddings show-text <ID> --type <TYPE>
```

**Arguments:**
- `<ID>` (required) - Standard or Objective ID (e.g., "2.CN.1" or "2.CN.1.1")

**Options:**
- `--type <TYPE>, -t <TYPE>` - Type of item: "standard" or "objective" (default: "standard")

**Examples:**
```bash
# View prepared text for a standard
pocketmusec embeddings show-text 2.CN.1 --type standard

# View prepared text for an objective
pocketmusec embeddings show-text 2.CN.1.1 --type objective
```

**Use Cases:**
- Debug embedding quality issues
- Review text formatting before API calls
- Understand how standards and objectives are combined
- Tweak extraction results by examining prepared content

### `embeddings clear-texts` - Remove Prepared Text Files

Delete all prepared text files from the `data/prepared_texts/` directory.

```bash
pocketmusec embeddings clear-texts
```

**Note:** This only removes text files, not embeddings from the database.

---

## 4. Utility Commands

### `version` - Show Version Information

Display current PocketMusec version.

```bash
pocketmusec version
```

**Output:**
```
pocketmusec v0.1.0
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
DATABASE_PATH=./data/pocket_musec.db

# Logging Configuration
LOG_LEVEL=INFO
```

### Default File Locations

- **Database:** `./data/pocket_musec.db` (created automatically)
- **Prepared Texts:** `./data/prepared_texts/` (created during embedding generation)
  - `standards/` - Prepared text for standards (grade + strand + standard + objectives)
  - `objectives/` - Prepared text for individual objectives
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

**5. Prepared Text Issues**
```
Error: Failed to save prepared text
```
- Check write permissions to `data/prepared_texts/`
- Ensure sufficient disk space
- Verify directory structure exists

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
    pocketmusec generate lesson --output "${grade}_lesson.md"
done
```

**Automated ingestion workflow:**
```bash
#!/bin/bash
# Ingest standards
pocketmusec ingest standards "NC Standards.pdf" --force

# Generate embeddings
pocketmusec embeddings generate --force

# Show statistics
pocketmusec embeddings stats

# Review prepared texts
pocketmusec embeddings texts
```

### Python Integration

```python
import subprocess
import json

def generate_lesson(grade_level, output_file):
    """Generate lesson using CLI from Python"""
    cmd = [
        "pocketmusec", "generate", "lesson",
        "--output", output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def check_prepared_texts():
    """Check prepared texts status"""
    cmd = ["pocketmusec", "embeddings", "texts"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

# Usage
success = generate_lesson("3rd Grade", "grade3_lesson.md")
check_prepared_texts()
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