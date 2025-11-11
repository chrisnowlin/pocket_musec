# IngestionAgent Guide

## Overview

The **IngestionAgent** is a conversational agent built on the PocketFlow framework that handles document ingestion through an interactive dialogue. It integrates with the existing document classification and parsing infrastructure to provide a user-friendly way to ingest NC Music Education documents.

## Architecture

### Components

1. **IngestionAgent** (`backend/pocketflow/ingestion_agent.py`)
   - Conversational agent that guides users through document ingestion
   - Manages conversation state and context
   - Integrates with DocumentClassifier and parsers

2. **Ingestion Nodes** (`backend/pocketflow/ingestion_nodes.py`)
   - Reusable workflow nodes for PocketFlow pipelines
   - Can be composed into custom ingestion workflows
   - Includes validation, classification, and processing nodes

3. **Example Usage** (`examples/ingestion_agent_example.py`)
   - Demonstrates both conversational and workflow usage patterns

## Features

### Conversation States

The IngestionAgent manages the following states:

1. **welcome** - Initial greeting and instructions
2. **file_path** - File path collection and validation
3. **ingestion_options** - Confirmation and advanced options
4. **processing** - Document processing and ingestion
5. **complete** - Success/failure summary

### Document Type Support

- **Standards** - Formal NC Music Standards (fully implemented)
- **Unpacking** - Grade-level unpacking documents (placeholder)
- **Alignment** - Horizontal/Vertical alignment matrices (placeholder)
- **Reference** - Glossaries, FAQs, guides (placeholder)

### Automatic Features

- **File validation** - Checks path, extension, and file size
- **Document classification** - Automatic type detection with confidence scores
- **Parser routing** - Routes to appropriate parser based on document type
- **Database integration** - Saves ingested content to SQLite database
- **Error handling** - Graceful error recovery and user feedback

## Usage

### Conversational Usage

```python
from backend.pocketflow.flow import Flow
from backend.pocketflow.store import Store
from backend.pocketflow.ingestion_agent import IngestionAgent

# Create agent
flow = Flow("Ingestion Flow")
store = Store()
agent = IngestionAgent(flow, store)

# Start conversation
response = agent.chat("")  # Trigger welcome
print(response)

# Provide file path
response = agent.chat("/path/to/document.pdf")
print(response)

# Confirm ingestion
response = agent.chat("yes")
print(response)

# Get results
results = agent.get_ingestion_results()
print(f"Ingested {results['standards_count']} standards")
```

### Workflow Usage

```python
from backend.pocketflow.flow import Flow
from backend.pocketflow.ingestion_nodes import (
    FileValidationNode,
    DocumentClassificationNode,
    StandardsIngestionNode,
    IngestionSummaryNode
)

# Create workflow
flow = Flow("Document Ingestion")
flow.add_node(FileValidationNode())
flow.add_node(DocumentClassificationNode())
flow.add_node(StandardsIngestionNode())
flow.add_node(IngestionSummaryNode())

# Execute
result = flow.execute({"file_path": "/path/to/document.pdf"})
print(result["summary"])
```

## Available Nodes

### FileValidationNode
Validates PDF file paths and returns normalized file information.

**Input:**
```python
{"file_path": "/path/to/file.pdf"}
```

**Output:**
```python
{
    "valid": True,
    "absolute_path": "/absolute/path/to/file.pdf",
    "file_name": "file.pdf",
    "file_size": 12345
}
```

### DocumentClassificationNode
Classifies document type using the DocumentClassifier.

**Input:** Output from FileValidationNode

**Output:**
```python
{
    ...previous_data,
    "document_type": DocumentType.STANDARDS,
    "confidence": 0.95,
    "recommended_parser": "NCStandardsParser",
    "classification_success": True
}
```

### StandardsIngestionNode
Ingests standards documents and saves to database.

**Input:** Output from DocumentClassificationNode

**Output:**
```python
{
    ...previous_data,
    "ingestion_success": True,
    "standards_count": 80,
    "objectives_count": 200,
    "statistics": {...}
}
```

### IngestionRouterNode
Routes documents to appropriate processor based on type.

**Input:** Output from DocumentClassificationNode

**Output:**
```python
{
    ...previous_data,
    "route_to": "StandardsIngestion"
}
```

### IngestionSummaryNode
Generates a summary of ingestion results.

**Input:** Output from any ingestion node

**Output:**
```python
{
    ...previous_data,
    "summary": {
        "file_name": "standards.pdf",
        "document_type": "standards",
        "confidence": 0.95,
        "success": True,
        "standards_count": 80,
        "objectives_count": 200
    }
}
```

## Conversation Flow

```
┌─────────────────┐
│    Welcome      │
│  (show options) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   File Path     │
│ (validate file) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Classification  │
│ (analyze type)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ing. Options    │
│ (confirm/opts)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Processing    │
│ (ingest data)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Complete     │
│ (show results)  │
└─────────────────┘
```

## Commands

At any point in the conversation, users can:

- **quit / exit / q** - Cancel ingestion and exit
- **back / b** - Return to previous state
- **yes / y** - Confirm action
- **no / n** - Decline action
- **options** - Show advanced options (when available)

## Advanced Options

When at the ingestion options state, users can:

1. Choose vision AI processing (slower, more accurate)
2. Choose fast table-based processing (faster, less accurate)
3. Force re-ingestion (overwrite existing data)
4. Preview extraction results

## Integration with Existing CLI

The IngestionAgent can be integrated into the existing CLI:

```python
# In cli/commands/ingest.py
@ingest_app.command()
def interactive(
    db_path: str = typer.Option(None, "--db-path", help="Database path")
):
    """Interactive document ingestion using conversational agent"""
    flow = Flow("Interactive Ingestion")
    store = Store()
    
    db_manager = DatabaseManager(db_path) if db_path else None
    agent = IngestionAgent(flow, store, db_manager=db_manager)
    
    # Start conversation
    response = agent.chat("")
    console.print(response)
    
    # Conversation loop
    while agent.get_state() != "complete":
        user_input = typer.prompt("\nYou")
        response = agent.chat(user_input)
        console.print(response)
```

## Testing

Run the simple test suite:

```bash
python test_ingestion_agent_simple.py
```

Expected output:
```
✅ All tests passed!
🎉 All IngestionAgent tests passed!
```

## Future Enhancements

### Planned Features

1. **Unpacking Document Support**
   - Implement UnpackingIngestionNode
   - Extract teaching strategies and assessment examples
   - Link to related standards

2. **Alignment Document Support**
   - Implement AlignmentIngestionNode
   - Extract relationships between standards
   - Build progression maps

3. **Reference Document Support**
   - Implement ReferenceIngestionNode
   - Extract glossary terms and definitions
   - Parse FAQ format

4. **Advanced Options**
   - Preview mode (dry run without saving)
   - Batch ingestion (multiple files)
   - Progress tracking for large files
   - Resume interrupted ingestions

5. **API Integration**
   - REST endpoints for ingestion
   - WebSocket support for real-time progress
   - Integration with frontend UI

## Comparison with Existing CLI

| Feature | CLI Ingest Command | IngestionAgent |
|---------|-------------------|----------------|
| Interface | Command-line arguments | Conversational |
| Guidance | Minimal | Step-by-step |
| Validation | After submission | Real-time |
| Error Recovery | Restart required | Context preserved |
| Document Detection | Manual `auto` command | Automatic |
| Progress Feedback | Basic | Detailed |

## API Reference

### IngestionAgent

#### Methods

- **`chat(message: str) -> str`** - Process user message and return response
- **`get_ingestion_context() -> Dict`** - Get current ingestion context
- **`get_ingestion_results() -> Optional[Dict]`** - Get results of last ingestion
- **`reset_ingestion() -> None`** - Reset for new document

#### Properties

- **`current_state: str`** - Current conversation state
- **`ingestion_context: Dict`** - Contextual data for current ingestion

### Example: Custom Workflow

```python
from backend.pocketflow.flow import Flow
from backend.pocketflow.ingestion_nodes import *

# Create custom workflow with conditional routing
class ConditionalRouter(Node):
    def process(self, data):
        doc_type = data["document_type"]
        
        if doc_type == DocumentType.STANDARDS:
            # Route to standards processor
            return StandardsIngestionNode().process(data)
        elif doc_type == DocumentType.UNPACKING:
            # Route to unpacking processor
            return UnpackingIngestionNode().process(data)
        else:
            # Skip unsupported types
            return {"skipped": True, "reason": "Unsupported type"}

# Build workflow
flow = Flow("Smart Ingestion")
flow.add_node(FileValidationNode())
flow.add_node(DocumentClassificationNode())
flow.add_node(ConditionalRouter())
flow.add_node(IngestionSummaryNode())
```

## Troubleshooting

### Common Issues

**Problem:** Import errors for IngestionAgent

**Solution:** Ensure you're importing from the correct path:
```python
from backend.pocketflow.ingestion_agent import IngestionAgent
```

**Problem:** File validation fails

**Solution:** Use absolute paths or ensure the file exists:
```python
from pathlib import Path
file_path = str(Path("document.pdf").resolve())
```

**Problem:** Database connection errors

**Solution:** Ensure database is initialized before ingestion:
```python
db_manager = DatabaseManager()
db_manager.initialize_database()
```

## Contributing

When extending the IngestionAgent:

1. Add new states to `_setup_state_handlers()`
2. Create corresponding handler methods (`_handle_<state>`)
3. Update conversation flow documentation
4. Add tests for new functionality
5. Update this guide

## Support

For issues or questions:
- Check test suite: `python test_ingestion_agent_simple.py`
- Review conversation state: `agent.get_state()`
- Inspect context: `agent.get_ingestion_context()`
- Enable debug logging: `export LOG_LEVEL=DEBUG`
