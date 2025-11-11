# Design Document: Milestone 1 Architecture

## Overview

This document outlines the technical design for Milestone 1, which establishes the foundation for standards-based lesson generation through a CLI interface.

## System Architecture

```
┌─────────────────────────────────────────────┐
│             CLI Interface (Typer)           │
│                                             │
│  • pocketflow ingest standards             │
│  • pocketflow generate lesson              │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│          PocketFlow Framework               │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Node   │──│   Flow   │──│  Store   │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│                                             │
│  ┌────────────────────────────────────────┐│
│  │         LessonAgent                    ││
│  │  • Conversation management             ││
│  │  • Requirements gathering              ││
│  │  • Prompt orchestration                ││
│  └────────────────────────────────────────┘│
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│            Core Services                    │
│                                             │
│  ┌─────────────┐      ┌─────────────────┐ │
│  │  Standards  │      │   Chutes LLM    │ │
│  │  Repository │      │   Integration   │ │
│  └──────┬──────┘      └─────────────────┘ │
│         │                                   │
│  ┌──────▼──────────────────────────────┐   │
│  │     SQLite Database                 │   │
│  │  • standards table                  │   │
│  │  • objectives table                 │   │
│  │  • embeddings (future)              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Data Flow

### Standards Ingestion Pipeline

1. **PDF Input** → NC standards PDFs from `NC Music Standards and Resources/`
2. **Parser** → pdfplumber extracts text with positional analysis
3. **Normalizer** → Maps to canonical schema (grade, strand, standard, objectives)
4. **Persister** → Stores in SQLite with proper relationships
5. **Cache** → JSON representation for quick access

### Lesson Generation Flow

1. **Chat Interface** → Teacher provides requirements interactively
2. **Agent Processing** → LessonAgent validates and guides selection
3. **Standards Lookup** → Repository queries matching standards
4. **Prompt Construction** → Combines requirements with standards context
5. **LLM Generation** → Chutes API generates lesson content
6. **Draft Management** → Stores in temporary workspace
7. **Editor Launch** → Opens system editor for refinement
8. **Save/Export** → Teacher selects final destination

## Database Schema

```sql
-- Core standards storage
CREATE TABLE standards (
    standard_id TEXT PRIMARY KEY,      -- e.g., "K.CN.1"
    grade_level TEXT NOT NULL,         -- K, 1-8, BE, IN, AC, AD
    strand_code TEXT NOT NULL,         -- CN, CR, PR, RE
    strand_name TEXT NOT NULL,         -- Connect, Create, Present, Respond
    strand_description TEXT NOT NULL,
    standard_text TEXT NOT NULL,
    source_document TEXT,
    ingestion_date TEXT,
    version TEXT
);

CREATE TABLE objectives (
    objective_id TEXT PRIMARY KEY,     -- e.g., "K.CN.1.1"
    standard_id TEXT NOT NULL,
    objective_text TEXT NOT NULL,
    FOREIGN KEY (standard_id) REFERENCES standards(standard_id)
);

-- Indexes for common queries
CREATE INDEX idx_grade_level ON standards(grade_level);
CREATE INDEX idx_strand_code ON standards(strand_code);
CREATE INDEX idx_standard_objectives ON objectives(standard_id);
```

## PocketFlow Agent Design

### Core Components

```python
class Node:
    """Basic unit of computation in the graph"""
    def process(self, input_data: Any) -> Any:
        pass

class Flow:
    """Orchestrates node execution"""
    def add_node(self, node: Node) -> None:
        pass
    
    def execute(self, initial_input: Any) -> Any:
        pass

class Store:
    """Maintains conversation context"""
    def get(self, key: str) -> Any:
        pass
    
    def set(self, key: str, value: Any) -> None:
        pass

class Agent:
    """Base class for conversational agents"""
    def __init__(self, flow: Flow, store: Store):
        self.flow = flow
        self.store = store
    
    def chat(self, message: str) -> str:
        pass
```

### LessonAgent Implementation

```python
class LessonAgent(Agent):
    """Specialized agent for lesson generation"""
    
    def __init__(self, standards_repo, llm_client):
        super().__init__()
        self.standards_repo = standards_repo
        self.llm_client = llm_client
        self.conversation_state = "grade_selection"
    
    def chat(self, message: str) -> str:
        # State machine for conversation flow
        if self.conversation_state == "grade_selection":
            return self.handle_grade_selection(message)
        elif self.conversation_state == "strand_selection":
            return self.handle_strand_selection(message)
        # ... additional states
```

## File Organization

```
pocket_musec/
├── backend/
│   ├── pocketflow/
│   │   ├── __init__.py
│   │   ├── node.py
│   │   ├── flow.py
│   │   ├── store.py
│   │   └── agent.py
│   ├── agents/
│   │   └── lesson_agent.py
│   ├── ingestion/
│   │   ├── pdf_parser.py
│   │   └── standards_normalizer.py
│   ├── repositories/
│   │   └── standards_repository.py
│   └── integrations/
│       └── chutes_client.py
├── cli/
│   ├── __init__.py
│   ├── main.py
│   ├── commands/
│   │   ├── ingest.py
│   │   └── generate.py
│   └── utils/
│       ├── editor.py
│       └── session.py
├── data/
│   ├── standards/
│   │   ├── standards.db
│   │   └── cache/
│   └── temp/
│       └── sessions/
└── tests/
    ├── test_pocketflow/
    ├── test_ingestion/
    └── test_cli/
```

## Conversation State Machine

```
START
  │
  ▼
GRADE_SELECTION ──invalid──> GRADE_SELECTION
  │                              ▲
  │valid                         │retry
  ▼                              │
STRAND_SELECTION ──invalid──────┘
  │
  │valid
  ▼
STANDARD_RECOMMENDATION
  │
  │select
  ▼
OBJECTIVE_REFINEMENT
  │
  │optional
  ▼
ADDITIONAL_CONTEXT
  │
  │skip/provide
  ▼
CONFIRMATION ──back──> [Previous State]
  │           └─quit──> END
  │generate
  ▼
GENERATION
  │
  ▼
EDITOR_LAUNCH
  │
  ▼
POST_EDIT_OPTIONS
  │
  ├─save──────> SAVE_DIALOG ──> SESSION_SUMMARY
  ├─regenerate─> GENERATION
  └─cancel─────> SESSION_SUMMARY
                        │
                        ▼
                       END
```

## Key Design Decisions

### 1. Synchronous CLI Interaction
- Use blocking I/O for simplicity in CLI context
- No need for async complexity in single-user tool
- Editor launch requires synchronous wait anyway

### 2. Stateless Agent Between Sessions
- Each CLI invocation starts fresh
- Draft history only persists within session
- Reduces complexity and storage requirements

### 3. Flat Standards Schema
- Denormalized for query performance
- Single source of truth in SQLite
- JSON cache for repeated access patterns

### 4. Minimal PocketFlow Framework
- 100-line core keeps it maintainable
- Just enough abstraction for agent needs
- No external dependencies on heavy frameworks

### 5. Progressive Enhancement Strategy
- Milestone 1 uses system defaults (editor, paths)
- Configuration options deferred to later milestones
- Focus on core functionality first

## Performance Considerations

- **Ingestion**: One-time operation, can be slower (~30s for all PDFs acceptable)
- **Standards Query**: Index on grade/strand for <10ms response
- **LLM Generation**: 5-10s expected, show progress indicator
- **Editor Launch**: Instant, using system defaults
- **Session Cleanup**: Automatic on exit, <1s

## Security & Privacy

- **Local Data**: All standards data stored locally
- **API Keys**: Environment variables, never in code
- **Temp Files**: Cleared on session exit
- **No Telemetry**: No usage tracking in Milestone 1
- **File Permissions**: Respect OS user permissions

## Testing Strategy

### Unit Tests
- PocketFlow components (Node, Flow, Store, Agent)
- PDF parser with sample documents
- Standards repository queries
- Session management utilities

### Integration Tests
- Full ingestion pipeline with real PDFs
- End-to-end CLI conversation flow
- Editor launch and file save
- Draft history management

### Regression Tests
- Lesson quality for each grade level
- Standards alignment accuracy
- Objective coverage validation

## Future Considerations (Post-Milestone 1)

- **Vector Embeddings**: Add sqlite-vec for semantic search
- **Local LLM**: Support for offline generation
- **Web UI**: Electron app with React frontend
- **Cloud Sync**: Optional backup of lessons
- **Multi-format Export**: Word, PDF, HTML outputs
- **Collaboration**: Share lessons between teachers