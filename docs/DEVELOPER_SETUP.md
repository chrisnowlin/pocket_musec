# PocketMusec Developer Setup Guide

## Overview

PocketMusec is a Python-based CLI application for AI-powered music lesson planning. This guide covers everything developers need to set up, develop, test, and contribute to the project.

## System Requirements

### Minimum Requirements
- **Python:** 3.9 or higher
- **Operating System:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB free space for dependencies and data
- **Internet:** Required for API calls and package installation

### Recommended Development Environment
- **IDE:** VS Code, PyCharm, or similar with Python support
- **Terminal:** Modern terminal with UTF-8 support
- **Git:** Version 2.30 or higher
- **Database Tool:** DB Browser for SQLite (optional)

---

## Quick Start Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/pocket_musec.git
cd pocket_musec
```

### 2. Install uv Package Manager
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or follow instructions at https://github.com/astral-sh/uv
```

### 3. Install Dependencies
```bash
uv install
```

### 4. Set Up Environment
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 5. Verify Installation
```bash
uv run python main.py --help
```

---

## Detailed Setup Instructions

### Python Environment Setup

#### Using uv (Recommended)
```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv install

# Install development dependencies
uv install --dev
```

#### Using pip (Alternative)
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate   # macOS/Linux
# or
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Environment Configuration

Create `.env` file in project root:

```bash
# Required: Chutes API Configuration
CHUTES_API_KEY=your_chutes_api_key_here
CHUTES_BASE_URL=https://api.chutes.ai

# Optional: Database Configuration
DATABASE_PATH=./data/standards.db

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/pocketmusec.log

# Optional: Development Settings
DEBUG=False
TESTING=False
```

#### Getting API Keys

1. **Chutes API:**
   - Visit https://chutes.ai/developer
   - Create account and generate API key
   - Add key to `.env` file

2. **Testing API Keys:**
   - Use test keys for development
   - Never commit real API keys to repository

### Database Setup

#### SQLite (Default)
```bash
# Create data directory
mkdir -p data logs

# Database will be created automatically on first run
uv run python main.py ingest standards path/to/standards.pdf
```

#### Custom Database Location
```bash
# Set custom path in .env
DATABASE_PATH=/custom/path/standards.db

# Or use command line option
pocketflow ingest standards standards.pdf --db-path /custom/path/standards.db
```

---

## Development Workflow

### Project Structure
```
pocket_musec/
├── backend/                 # Core application logic
│   ├── ingestion/          # PDF parsing and standards ingestion
│   ├── llm/               # AI/LLM integration
│   ├── pocketflow/        # Conversation flow framework
│   ├── repositories/      # Database layer
│   └── utils/             # Utility functions
├── cli/                   # Command-line interface
│   ├── commands/         # CLI command implementations
│   └── main.py          # CLI entry point
├── tests/                # Test suite
│   ├── test_integration/
│   ├── test_regression/
│   └── fixtures/
├── docs/                 # Documentation
├── data/                 # Database and data files
└── logs/                 # Application logs
```

### Running the Application

#### Development Mode
```bash
# Run CLI with uv
uv run python main.py --help

# Or activate environment first
source .venv/bin/activate
python main.py --help
```

#### Testing Commands
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_pocketflow/test_agent.py

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run integration tests
uv run pytest tests/test_integration/
```

### Code Quality Tools

#### Linting
```bash
# Run ruff linter
uv run ruff check backend/ cli/ tests/

# Auto-fix issues
uv run ruff check --fix backend/ cli/ tests/

# Run flake8 (if configured)
uv run flake8 backend/ cli/ tests/
```

#### Type Checking
```bash
# Run mypy type checker
uv run mypy backend/ cli/ tests/

# Check specific module
uv run mypy backend/pocketflow/agent.py
```

#### Formatting
```bash
# Format code with black
uv run black backend/ cli/ tests/

# Format imports with isort
uv run isort backend/ cli/ tests/
```

---

## Testing Strategy

### Test Categories

#### 1. Unit Tests
- Test individual functions and classes
- Fast execution, no external dependencies
- Located in `tests/test_*/`

#### 2. Integration Tests
- Test component interactions
- Database and API integration
- Located in `tests/test_integration/`

#### 3. Regression Tests
- Prevent quality degradation
- Lesson quality metrics
- Located in `tests/test_regression/`

### Running Tests

#### Full Test Suite
```bash
# Run all tests with coverage
uv run pytest --cov=backend --cov-report=term-missing

# Run with verbose output
uv run pytest -v

# Run specific test categories
uv run pytest tests/test_integration/
uv run pytest tests/test_regression/
```

#### Test Configuration
```bash
# Create pytest.ini if needed
echo "[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --disable-warnings" > pytest.ini
```

### Writing Tests

#### Test Structure Example
```python
# tests/test_pocketflow/test_agent.py
import pytest
from unittest.mock import Mock, patch
from backend.pocketflow.agent import Agent

class TestAgent:
    def setup_method(self):
        """Setup for each test method"""
        self.mock_flow = Mock()
        self.mock_store = Mock()
        self.agent = Agent(self.mock_flow, self.mock_store)
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        assert self.agent.flow == self.mock_flow
        assert self.agent.store == self.mock_store
    
    @patch('backend.pocketflow.agent.external_service')
    def test_agent_with_external_dependency(self, mock_service):
        """Test agent with mocked external service"""
        mock_service.return_value = "mocked response"
        result = self.agent.call_external_service()
        assert result == "mocked response"
```

#### Fixtures and Data
```python
# tests/fixtures/standards_fixtures.py
import pytest

@pytest.fixture
def sample_standard():
    """Provide sample standard for testing"""
    return {
        "standard_id": "CN.K.1",
        "grade_level": "Kindergarten",
        "strand_code": "CN",
        "standard_text": "Sample standard text"
    }

@pytest.fixture
def mock_database():
    """Provide in-memory database for testing"""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    # Setup database schema
    yield conn
    conn.close()
```

---

## Development Guidelines

### Code Style

#### Python Style Guide
- Follow PEP 8 for Python code
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints where possible

#### Naming Conventions
```python
# Classes: PascalCase
class StandardsParser:
    pass

# Functions and variables: snake_case  
def parse_standards_document():
    standard_count = 0

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Private methods: prefix with underscore
def _internal_helper_method():
    pass
```

#### Documentation Standards
```python
def parse_standards_document(pdf_path: str) -> List[ParsedStandard]:
    """
    Parse NC music standards from PDF document.
    
    Args:
        pdf_path: Path to the PDF file containing standards
        
    Returns:
        List of parsed standards with objectives
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ParseError: If PDF cannot be parsed
        
    Example:
        >>> standards = parse_standards_document("standards.pdf")
        >>> len(standards)
        150
    """
    pass
```

### Git Workflow

#### Branch Naming
```bash
# Feature branches
feature/lesson-generation
feature/pdf-parser-improvements

# Bugfix branches  
bugfix/standards-ingestion-error
bugfix/memory-leak-fix

# Release branches
release/v0.1.0
release/v0.2.0
```

#### Commit Messages
```bash
# Format: type(scope): description
feat(cli): add interactive lesson generation
fix(parser): handle malformed PDF files
docs(readme): update installation instructions
test(ingestion): add integration tests for PDF parsing
refactor(database): extract connection logic to manager
```

#### Pull Request Template
```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Error Handling

#### Exception Handling Patterns
```python
# Use specific exceptions
try:
    result = parse_pdf(file_path)
except FileNotFoundError as e:
    logger.error(f"PDF file not found: {file_path}")
    raise FileNotFoundError(f"Cannot find standards PDF: {file_path}") from e
except ParseError as e:
    logger.warning(f"PDF parsing failed, trying fallback: {e}")
    result = fallback_parser(file_path)

# Custom exceptions
class StandardsParsingError(Exception):
    """Raised when standards parsing fails"""
    pass

# Use context managers for resources
with open(file_path, 'r') as f:
    content = f.read()
    # Process content
```

#### Logging Standards
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened, but program continues")
logger.error("Serious problem, program may not continue")
logger.critical("Very serious error, program cannot continue")

# Include context in log messages
logger.info(f"Processing standards for grade {grade_level}")
logger.error(f"Failed to parse PDF {file_path}: {error_message}")
```

---

## Database Development

### Schema Management

#### Database Initialization
```python
# backend/repositories/database.py
class DatabaseManager:
    def initialize_database(self):
        """Create database tables and indexes"""
        with self.get_connection() as conn:
            # Read schema from file
            schema_path = Path(__file__).parent / "schema.sql"
            schema = schema_path.read_text()
            conn.executescript(schema)
            conn.commit()
```

#### Migration Strategy
```bash
# Version 1: Initial schema
# backend/repositories/migrations/001_initial_schema.sql

# Version 2: Add embeddings table  
# backend/repositories/migrations/002_add_embeddings.sql

# Migration script
python -m backend.repositories.migrations migrate
```

### Testing Database Code

#### In-Memory Testing
```python
@pytest.fixture
def test_db():
    """Create in-memory database for testing"""
    manager = DatabaseManager(":memory:")
    manager.initialize_database()
    return manager

def test_standards_repository(test_db):
    """Test repository with in-memory database"""
    repo = StandardsRepository(test_db)
    # Test operations
```

#### Test Data Management
```python
# tests/fixtures/test_data.py
def create_test_standards(db_connection):
    """Create test standards for integration tests"""
    standards = [
        ("CN.K.1", "Kindergarten", "CN", "Creating Music", ...),
        ("PR.1.1", "1st Grade", "PR", "Performing Music", ...),
    ]
    
    db_connection.executemany(
        "INSERT INTO standards VALUES (?, ?, ?, ?, ?)",
        standards
    )
    db_connection.commit()
```

---

## API Integration Development

### Working with External APIs

#### Configuration Management
```python
# backend/config.py
import os
from typing import Optional

class Config:
    CHUTES_API_KEY: str = os.getenv("CHUTES_API_KEY", "")
    CHUTES_BASE_URL: str = os.getenv("CHUTES_BASE_URL", "https://api.chutes.ai")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        return bool(cls.CHUTES_API_KEY)
```

#### API Client Pattern
```python
# backend/llm/chutes_client.py
import requests
from typing import Dict, Any
import time

class ChutesClient:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.CHUTES_API_KEY}",
            "Content-Type": "application/json"
        })
    
    def generate_lesson(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate lesson using Chutes API"""
        payload = {"prompt": prompt, **kwargs}
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.post(
                    f"{self.config.CHUTES_BASE_URL}/generate",
                    json=payload,
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                if attempt == self.config.MAX_RETRIES - 1:
                    raise APIError(f"API request failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
```

### Mocking APIs for Testing

#### Using unittest.mock
```python
# tests/test_llm/test_chutes_client.py
from unittest.mock import Mock, patch
import pytest

@patch('backend.llm.chutes_client.requests.Session.post')
def test_generate_lesson_success(mock_post):
    """Test successful lesson generation"""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = {"lesson": "Generated lesson content"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    # Test client
    client = ChutesClient()
    result = client.generate_lesson("Test prompt")
    
    assert result["lesson"] == "Generated lesson content"
    mock_post.assert_called_once()
```

---

## Performance Optimization

### Profiling and Monitoring

#### Performance Profiling
```bash
# Profile CLI performance
uv run python -m cProfile -o profile.stats main.py generate lesson

# Analyze profile results
uv run python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

#### Memory Profiling
```bash
# Install memory profiler
uv install memory-profiler

# Profile memory usage
uv run python -m memory_profiler main.py generate lesson
```

### Database Optimization

#### Query Optimization
```python
# Use indexes effectively
def get_standards_by_grade_and_strand(grade: str, strand: str):
    """Optimized query using indexes"""
    query = """
    SELECT * FROM standards 
    WHERE grade_level = ? AND strand_code = ?
    ORDER BY standard_id
    """
    return self.conn.execute(query, (grade, strand)).fetchall()

# Batch operations for better performance
def insert_standards_batch(standards: List[Standard]):
    """Insert multiple standards efficiently"""
    data = [(s.standard_id, s.grade_level, s.strand_code, ...) 
            for s in standards]
    self.conn.executemany(INSERT_QUERY, data)
    self.conn.commit()
```

#### Caching Strategy
```python
from functools import lru_cache
from typing import List

class StandardsRepository:
    @lru_cache(maxsize=128)
    def get_standards_by_grade(self, grade: str) -> List[Standard]:
        """Cache frequently accessed standards"""
        # Database query
        pass
    
    def clear_cache(self):
        """Clear cache when data changes"""
        self.get_standards_by_grade.cache_clear()
```

---

## Debugging and Troubleshooting

### Debugging Setup

#### VS Code Configuration
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug CLI",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "args": ["generate", "lesson"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### Logging Configuration
```python
# backend/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """Configure logging for development"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers
    )
```

### Common Development Issues

#### Import Path Issues
```python
# Add project root to Python path for development
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

#### Database Lock Issues
```python
# Use connection pooling and proper connection management
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
    
    def get_connection(self):
        """Get thread-safe database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
        return self._connection
```

#### API Rate Limiting
```python
import time
from typing import Callable

def rate_limit(calls_per_second: float):
    """Decorator to rate limit API calls"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

---

## Deployment and Distribution

### Building for Distribution

#### Creating Executable
```bash
# Install PyInstaller
uv install pyinstaller

# Build executable
uv run pyinstaller --onefile main.py --name pocketflow

# Build with icon and additional data
uv run pyinstaller --onefile --windowed \
  --icon=assets/icon.ico \
  --add-data="backend:backend" \
  --add-data="cli:cli" \
  main.py
```

#### Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY uv.lock pyproject.toml ./
RUN pip install uv && uv install --system

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data logs

# Set entrypoint
ENTRYPOINT ["python", "main.py"]
```

### Environment-Specific Configuration

#### Development Environment
```bash
# .env.development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_PATH=./data/dev_standards.db
CHUTES_BASE_URL=https://api-staging.chutes.ai
```

#### Production Environment
```bash
# .env.production
DEBUG=False
LOG_LEVEL=INFO
DATABASE_PATH=/var/lib/pocketmusec/standards.db
CHUTES_BASE_URL=https://api.chutes.ai
```

---

## Contributing Guidelines

### Before Contributing

1. **Set up development environment** following this guide
2. **Run existing tests** to ensure everything works
3. **Create issue** describing your proposed change
4. **Get approval** before starting major work

### Making Changes

1. **Create feature branch** from main
2. **Write tests** for new functionality
3. **Implement changes** following code style guidelines
4. **Update documentation** as needed
5. **Run full test suite** and ensure all tests pass
6. **Submit pull request** with detailed description

### Code Review Process

1. **Automated checks** must pass (linting, formatting, tests)
2. **Manual review** by at least one maintainer
3. **Address feedback** and update as needed
4. **Approval required** before merging
5. **Squash commits** for clean history

### Release Process

1. **Update version** in pyproject.toml
2. **Update CHANGELOG.md** with release notes
3. **Create release tag** in Git
4. **Build and test** distribution packages
5. **Deploy to production** (if applicable)
6. **Announce release** to users

---

## Getting Help

### Documentation Resources
- **CLI Commands:** `docs/CLI_COMMANDS.md`
- **User Guide:** `docs/TEACHER_GUIDE.md`
- **API Documentation:** Inline docstrings and type hints

### Community Support
- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas
- **Wiki:** Community-maintained documentation

### Development Team
- **Maintainers:** Review pull requests and manage releases
- **Contributors:** Submit code and documentation improvements
- **Users:** Provide feedback and report issues

---

## Quick Reference

### Essential Commands
```bash
# Setup
uv install
cp .env.example .env

# Development
uv run python main.py --help
uv run pytest
uv run ruff check --fix

# Testing
uv run pytest tests/test_integration/
uv run pytest --cov=backend

# Building
uv run pyinstaller --onefile main.py
```

### Common File Locations
- **Main entry point:** `cli/main.py`
- **CLI commands:** `cli/commands/`
- **Core logic:** `backend/`
- **Tests:** `tests/`
- **Documentation:** `docs/`
- **Configuration:** `.env`

### Environment Variables
- `CHUTES_API_KEY`: Required for AI functionality
- `DATABASE_PATH`: SQLite database location
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `DEBUG`: Enable debug mode (True/False)

---

This setup guide provides everything developers need to start working with PocketMusec. For specific implementation details, refer to the inline code documentation and existing test cases.