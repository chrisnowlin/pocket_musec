# PocketMusec Documentation

Welcome to the PocketMusec documentation hub. PocketMusec is an AI-powered lesson planning assistant designed specifically for music education teachers.

## 📚 Documentation Overview

### For Users & Teachers
- **[Teacher Guide](TEACHER_GUIDE.md)** - Complete user guide for music educators
- **[Quick Start](#quick-start)** - Get up and running in minutes
- **[FAQ](#frequently-asked-questions)** - Common questions and solutions

### For Developers & Technical Staff
- **[CLI Commands Reference](CLI_COMMANDS.md)** - Complete command documentation
- **[Developer Setup Guide](DEVELOPER_SETUP.md)** - Development environment and contribution guide
- **[API Documentation](#api-documentation)** - Technical API reference
- **[Web Search Integration](WEB_SEARCH_INTEGRATION.md)** - Comprehensive web search capabilities guide
- **[Web Search Configuration](WEB_SEARCH_CONFIGURATION.md)** - Quick reference for search configuration
- **[File Storage System](FILE_STORAGE_SYSTEM.md)** - Comprehensive file storage documentation
- **[Developer File Storage Guide](DEVELOPER_FILE_STORAGE.md)** - Developer guide for file storage

### For System Administrators
- **[Installation & Deployment](DEVELOPER_SETUP.md#deployment-and-distribution)** - System setup requirements
- **[Configuration](DEVELOPER_SETUP.md#environment-configuration)** - Environment variables and settings
- **[File Storage Migration](FILE_STORAGE_MIGRATION.md)** - Migration guide for file storage system
- **[Troubleshooting](#troubleshooting)** - Common technical issues

---

## 🚀 Quick Start

### 1. Install PocketMusec
```bash
# Clone the repository
git clone https://github.com/your-org/pocket_musec.git
cd pocket_musec

# Install dependencies
uv install

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Generate Your First Lesson
```bash
pocketmusec generate lesson
```

That's it! You're ready to create standards-aligned music lessons.

---

## 🎵 For Music Teachers

### What PocketMusec Does
- ✅ **Saves Time** - Generate complete lesson plans in minutes through web interface
- ✅ **Standards Aligned** - Automatically matches NC music standards
- ✅ **Grade Specific** - Content tailored for K-12 music education
- ✅ **Four Music Strands** - Covers Creating, Performing, Responding, and Critical Response
- ✅ **Web-Based** - Access from any browser with no installation required
- ✅ **Enhanced Search** - Semantic search with advanced filtering and pagination
- ✅ **Web Search Integration** - Real-time educational content from trusted sources
- ✅ **Usage Analytics** - Track your lesson planning patterns and preferences

### Key Features
- **Web Interface** - Modern, responsive design accessible from any device
- **Interactive Lesson Generation** - Guided forms with real-time progress tracking
- **Standards-Based** - All lessons aligned with North Carolina music education standards
- **Smart Search** - Find standards using natural language queries with semantic understanding
- **Session Management** - Automatic saving and version history
- **Image Processing** - Upload and analyze sheet music with OCR and AI
- **File Storage System** - Permanent file storage with duplicate detection and organized directory structure
- **Embeddings Management** - Advanced semantic search with usage analytics
- **Web-Enhanced Lessons** - Integration of current educational content and research
- **Export Capabilities** - Download lessons and data in multiple formats

### Getting Started
1. **Read the [User Guide](USER_GUIDE.md)** for detailed web interface instructions
2. **Access the web interface** at `http://localhost:5173` after starting servers
3. **Configure your settings** for processing mode and preferences
4. **Start creating lessons** with the intuitive web forms
5. **Explore advanced features** like embeddings management and analytics

---

## 💻 For Developers

### Architecture Overview

PocketMusec features a **simplified, modular architecture** designed for maintainability and developer experience:

```
pocket_musec/
├── backend/                 # Core application logic
│   ├── api/               # FastAPI server and routes
│   ├── auth/              # Authentication system (simplified)
│   ├── citations/         # Citation tracking
│   ├── config.py          # Unified configuration management
│   ├── image_processing/  # Image OCR and vision analysis
│   ├── ingestion/         # Document parsing and standards ingestion
│   ├── llm/              # AI/LLM integration (Chutes API + Ollama)
│   ├── pocketflow/       # Conversation flow framework
│   ├── repositories/     # Database layer with unified migrations
│   └── utils/            # Utility functions
├── cli/                  # Command-line interface (Typer)
│   ├── commands/        # CLI command implementations
│   └── main.py         # CLI entry point
├── frontend/             # React TypeScript application
│   ├── src/
│   │   ├── components/  # Modular React components
│   │   ├── hooks/      # Custom React hooks
│   │   ├── pages/      # Page components
│   │   ├── types/      # TypeScript type definitions
│   │   └── constants/  # Static data and constants
├── electron/            # Electron desktop application
├── tests/              # Comprehensive test suite
├── docs/               # Documentation
└── data/              # SQLite database and files
```

### Recent Simplifications (v0.3.0)

The codebase has undergone significant simplification to improve maintainability:

- **Unified Configuration**: Centralized all configuration in [`backend/config.py`](../backend/config.py) with organized sections
- **Database Migration Consolidation**: Merged separate migration systems into a single [`MigrationManager`](../backend/repositories/migrations.py)
- **Frontend Component Refactoring**: Broke down the 1,630-line [`UnifiedPage.tsx`](../frontend/src/pages/UnifiedPage.tsx) into 17 focused components
- **State Management Organization**: Reorganized 18 separate state variables into logical groups (UI, Chat, LessonSettings, etc.)
- **Removed Unused Components**: Eliminated unused Zustand store and websocket client for cleaner architecture

### Technology Stack
- **Language:** Python 3.9+
- **CLI Framework:** Typer with Rich formatting
- **Database:** SQLite with custom repository layer
- **AI Integration:** Chutes API for lesson generation
- **PDF Processing:** pdfplumber for standards parsing
- **Testing:** pytest with comprehensive coverage
- **Package Management:** uv for fast dependency management

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-org/pocket_musec.git
cd pocket_musec
uv install

# Run tests
uv run pytest

# Development mode
uv run python main.py --help
```

See the [Developer Setup Guide](DEVELOPER_SETUP.md) for complete development instructions.

---

## 🌐 Web Interface Features

### Main Features
The web interface provides access to all PocketMusec functionality:

#### Lesson Generation
- **Guided Forms**: Step-by-step lesson creation with intuitive interface
- **Real-time Progress**: Visual feedback during AI generation
- **Rich Editor**: Built-in editing with auto-save and version history
- **Export Options**: Download lessons as Markdown or PDF

#### Image Management
- **Drag-and-Drop Upload**: Easy image ingestion with progress tracking
- **OCR Processing**: Automatic text extraction from sheet music
- **Vision AI Analysis**: Semantic understanding of musical content
- **Gallery View**: Organized display with search and filtering

#### File Storage Management
- **Permanent Storage**: Files stored with UUID-based naming to prevent conflicts
- **Duplicate Detection**: SHA256 hash-based detection prevents duplicate uploads
- **Organized Directory Structure**: Date-based organization (YYYY/MM/DD) for efficient management
- **Metadata Tracking**: Comprehensive metadata including file status, processing state, and user information
- **Security Features**: File type validation, size limits, and secure access controls
- **Cleanup Management**: Automated cleanup of old files with configurable retention policies

#### Embeddings Management
- **Semantic Search**: Natural language queries with advanced filtering
- **Pagination**: Efficient handling of large result sets
- **Virtual Scrolling**: Smooth performance with large lists
- **Usage Analytics**: Comprehensive tracking and insights
- **Export Features**: Download statistics and data in multiple formats
- **Batch Operations**: Bulk management with progress tracking

#### Settings & Configuration
- **Processing Modes**: Switch between Cloud (fast) and Local (private)
- **Model Management**: Download and monitor local AI models
- **Storage Configuration**: Manage quotas and cleanup options
- **User Preferences**: Customize interface and behavior

### Advanced Features
- **Accessibility**: Full WCAG 2.1 AA compliance
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Error Recovery**: Automatic retry with user-friendly messages
- **Performance Optimization**: Caching and efficient rendering

See the [User Guide](USER_GUIDE.md) for complete web interface documentation.

---

## 🔧 Configuration

PocketMusec uses a **unified configuration system** that centralizes all settings in [`backend/config.py`](../backend/config.py). This system provides organized configuration sections with sensible defaults.

### Environment Variables
Create a `.env` file in the project root:

```bash
# Required: Chutes API Configuration
CHUTES_API_KEY=your_chutes_api_key_here
CHUTES_API_BASE_URL=https://llm.chutes.ai/v1
CHUTES_EMBEDDING_BASE_URL=https://chutes-qwen-qwen3-embedding-8b.chutes.ai/v1

# Optional: API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: Database Configuration
DATABASE_PATH=./data/pocket_musec.db

# Optional: LLM Configuration
DEFAULT_MODEL=Qwen/Qwen3-VL-235B-A22B-Instruct
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000

# Optional: Ollama Local Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Optional: Image Processing Configuration
IMAGE_STORAGE_PATH=./data/images

# Optional: File Storage Configuration
FILE_STORAGE_ROOT=./data/uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif
DUPLICATE_DETECTION=true
FILE_RETENTION_DAYS=365
FILE_CLEANUP_ENABLED=true

# Optional: Logging Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false

# Optional: Web Search Configuration
BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here
BRAVE_SEARCH_CACHE_TTL=3600
BRAVE_SEARCH_MAX_CACHE_SIZE=100
BRAVE_SEARCH_TIMEOUT=30
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5

# Optional: Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### Configuration Sections

The unified configuration system organizes settings into logical sections:

- **APIConfig**: Server settings, CORS, API documentation
- **DatabaseConfig**: Database path and connection settings
- **ChutesConfig**: Cloud AI provider configuration
- **LLMConfig**: Language model parameters and defaults
- **OllamaConfig**: Local AI provider settings
- **ImageProcessingConfig**: File handling and storage limits
- **FileStorageConfig**: File storage settings and security configurations
- **WebSearchConfig**: Brave Search API and educational filtering settings
- **LoggingConfig**: Log levels, rotation, and formatting
- **SecurityConfig**: Authentication and demo mode settings
- **PathConfig**: Directory paths and file locations

### File Locations
- **Database:** `./data/pocket_musec.db` (created automatically)
- **File Storage:** `./data/uploads/` (permanent file storage with date-based organization)
- **Prepared Texts:** `./data/prepared_texts/` (saved during embedding generation)
- **Logs:** `./logs/pocketmusec.log` (configured in .env)
- **Temporary Files:** System temp directory (cleaned automatically)
- **Generated Lessons:** Current directory or specified path

---

## 🧪 Testing

### Test Categories
- **Unit Tests** - Individual component testing
- **Integration Tests** - End-to-end workflow testing  
- **Regression Tests** - Quality assurance and performance

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run specific test categories
uv run pytest tests/test_integration/
uv run pytest tests/test_regression/

# Verbose output
uv run pytest -v
```

### Test Data
- **Fixtures** in `tests/fixtures/` provide sample standards and lessons
- **Integration tests** use temporary databases for isolation
- **Regression tests** ensure quality standards are maintained

---

## 🎯 NC Music Standards Integration

### Supported Strands
PocketMusec supports all four NC music education strands:

1. **CN - Creating Music**
   - Composing and arranging
   - Improvisation and creativity
   - Songwriting and expression

2. **PR - Performing Music**
   - Instrumental and vocal performance
   - Ensemble participation
   - Technical skill development

3. **RE - Responding to Music**
   - Music appreciation and analysis
   - Cultural and historical context
   - Personal response to music

4. **CR - Critical Response**
   - Music evaluation and critique
   - Aesthetic judgment
   - Reflective thinking

### Grade Levels Supported
- **Elementary:** Kindergarten - 5th Grade
- **Middle School:** 6th Grade - 8th Grade  
- **High School:** 9th Grade - 12th Grade Music

### Standards Features
- **Automatic Alignment** - Lessons automatically reference appropriate standards
- **Objective Mapping** - Learning objectives linked to standard requirements
- **Semantic Search** - Find standards by meaning, not just codes
- **Cross-Reference** - See related standards and progressions

---

## 🔄 Workflow Examples

### Daily Lesson Planning
1. **Access Web Interface**: Navigate to `http://localhost:5173`
2. **Generate Morning Lesson**:
   - Click "New Lesson" in sidebar
   - Follow guided form for grade, strand, and standards
   - Add context about your students and resources
   - Generate and review AI-created lesson
3. **Plan Afternoon Lesson**:
   - Use "Similar Lessons" feature for related content
   - Generate with different strand or standard
   - Save with descriptive tags and folders
4. **Organize and Review**:
   - Access "Sessions" to see all lessons
   - Use search and filtering to find specific content
   - Export lessons for sharing or backup

### Unit Planning
1. **Search for Standards**:
   - Navigate to "Embeddings" → "Search"
   - Use natural language: "rhythm fundamentals for 3rd grade"
   - Apply filters for strand and grade level
2. **Generate Lesson Series**:
   - Use "Similar Lessons" for related standards
   - Create cohesive unit with multiple strands
   - Organize in unit folders with consistent naming
3. **Create Unit Overview**:
   - Export all lessons as a unit package
   - Add unit objectives and assessment plan
   - Share with colleagues or save for future use

### Curriculum Mapping
1. **Access Embeddings Dashboard**:
   - Navigate to "Embeddings" → "Statistics"
   - Review current standards coverage
   - Generate embeddings if needed
2. **Search Curriculum Topics**:
   - Use semantic search for broad concepts
   - Examples: "music notation", "ensemble skills", "composition techniques"
   - Export search results for curriculum documentation
3. **Analyze Usage Patterns**:
   - Review "Usage" tab for planning insights
   - Identify frequently used standards and topics
   - Optimize lesson planning based on data

---

## ❓ Frequently Asked Questions

### General Questions

**Q: Is PocketMusec free to use?**  
A: PocketMusec is open-source software, but requires an API key for the AI service (Chutes API) which has associated costs.

**Q: Can I use PocketMusec outside of North Carolina?**  
A: Currently, PocketMusec is optimized for NC music standards. Support for other state standards is planned for future releases.

**Q: Do I need internet access to use PocketMusec?**  
A: Yes, internet access is required for AI-powered lesson generation and standards search features.

### Technical Questions

**Q: What are the system requirements?**  
A: Python 3.9+, 4GB RAM minimum, 2GB storage space. See [Developer Setup Guide](DEVELOPER_SETUP.md#system-requirements) for details.

**Q: Can I use PocketMusec on a school computer without admin rights?**  
A: Yes, if Python and uv are available. The portable version doesn't require admin installation.

**Q: How are my lessons stored?**  
A: Lessons are saved as Markdown files on your local system. The standards database is stored locally in SQLite format.

### Usage Questions

**Q: Can I edit the generated lessons?**  
A: Yes! PocketMusec includes built-in editor integration and maintains draft history of all changes.

**Q: How do I share lessons with other teachers?**  
A: Lessons are saved as standard Markdown files that can be emailed, shared via cloud storage, or added to curriculum repositories.

**Q: Can PocketMusec create lessons for combined grade levels?**  
A: Yes, you can specify multi-grade contexts during the lesson generation process.

---

## 🐛 Troubleshooting

### Common Issues

#### Installation Problems
```bash
# If uv install fails, try:
python -m pip install --upgrade pip
pip install -r requirements.txt

# For permission errors:
uv install --user
```

#### API Connection Issues
```bash
# Check API key configuration
echo $CHUTES_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $CHUTES_API_KEY" https://api.chutes.ai/health

# Check network connectivity
ping api.chutes.ai
```

#### Database Issues
```bash
# Check database location
ls -la data/pocket_musec.db

# Recreate database if corrupted
rm data/pocket_musec.db
# Note: Document ingestion is no longer available - use existing data
```

#### Editor Integration Problems
```bash
# Set default editor explicitly
export EDITOR=nano  # or vim, code, etc.

# Test editor launch
$EDITOR test_file.txt
```

### Getting Help

1. **Check the logs** - Enable debug logging with `LOG_LEVEL=DEBUG`
2. **Review documentation** - Consult the relevant guide above
3. **Search issues** - Check GitHub Issues for similar problems
4. **Create issue** - Report bugs with detailed error messages and system information

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
pocketmusec generate lesson

# Run with Python debugger
uv run python -m pdb main.py generate lesson
```

---

## 📈 Performance & Optimization

### Tips for Better Performance

1. **Use embeddings search** - Faster than browsing standards manually
2. **Enable web search caching** - Configure longer TTL for frequently used searches
3. **Batch lesson generation** - Plan multiple lessons at once
4. **Local database** - Standards cached locally for fast access
5. **Optimize batch size** - Adjust `--batch-size` for your system
6. **Monitor web search performance** - Check cache hit rates and response times

### System Optimization
```bash
# Increase batch size for faster embedding generation
pocketmusec embeddings generate --batch-size 20

# Use custom database on faster storage
# Note: Document ingestion is no longer available - use existing data
# pocketmusec --db-path "/ssd/pocket_musec.db" generate lesson

# Clear old embeddings to free space
pocketmusec embeddings clear
pocketmusec embeddings generate

# Review prepared texts for quality debugging
pocketmusec embeddings texts
pocketmusec embeddings show-text <ID> --type standard
```

---

## 🤝 Contributing

We welcome contributions from the community! See the [Developer Setup Guide](DEVELOPER_SETUP.md#contributing-guidelines) for detailed instructions.

### Ways to Contribute
- **Report bugs** - Submit issues with detailed reproduction steps
- **Request features** - Suggest improvements and new capabilities
- **Submit code** - Fork, branch, and submit pull requests
- **Improve documentation** - Help us make the docs better
- **Share lessons** - Contribute example lessons and templates

### Development Process
1. **Set up development environment** following the setup guide
2. **Create issue** describing your proposed change
3. **Fork repository** and create feature branch
4. **Write tests** for new functionality
5. **Implement changes** following code style guidelines
6. **Submit pull request** with detailed description

---

## 📄 License

PocketMusec is released under the MIT License. See [LICENSE](../LICENSE) for full details.

### Third-Party Licenses
- **Typer** - MIT License
- **Rich** - MIT License  
- **pdfplumber** - MIT License
- **pytest** - MIT License
- **SQLite** - Public Domain

---

## 📞 Support & Contact

### Getting Help
- **Documentation:** Start with the guides above
- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas
- **Email:** support@pocketmusec.org (for institutional support)

### Community
- **Teachers Forum:** Share lesson ideas and best practices
- **Developer Chat:** Technical discussion and collaboration
- **Newsletter:** Updates and new feature announcements

### Professional Development
- **Training Workshops:** On-site and virtual training available
- **Implementation Support:** Help with district-wide deployment
- **Curriculum Consulting:** Standards alignment and lesson planning expertise

---

## 🗺️ Roadmap

### Current Version (v0.1.0)
- ✅ NC music standards ingestion
- ✅ Interactive lesson generation
- ✅ Four music strands support
- ✅ Editor integration and draft history
- ✅ Semantic standards search
- ✅ Prepared text inspection and debugging

### Planned Features
- 🔄 **Multi-state standards support** - Expand beyond NC standards
- 🔄 **Collaborative lesson planning** - Multiple teachers working together
- 🔄 **Assessment generation** - Create rubrics and evaluation tools
- 🔄 **Student progress tracking** - Monitor standards mastery
- 🔄 **Mobile app** - iOS and Android applications
- 🔄 **Learning management integration** - Canvas, Google Classroom, etc.

### Long-term Vision
- **AI-powered curriculum design** - Automated scope and sequence
- **Professional development tools** - Teacher training and resources
- **Student-facing applications** - Direct student learning tools
- **Analytics and insights** - Data-driven teaching improvements

---

## 📚 Additional Resources

### Music Education Standards
- [NC Department of Public Instruction - Arts Education](https://www.dpi.nc.gov/districts-schools/classroom-resources/arts-education)
- [National Core Arts Standards](https://www.nationalartsstandards.org/)
- [NAfME Music Standards](https://nafme.org/standards/)

### Professional Development
- [Music Educators Association](https://www.nafme.org/)
- [State Music Education Associations](https://www.artsedcollaborative.org/state-associations)
- [Teaching Music Resources](https://www.teachingmusic.org/)

### Technical Resources
- [Python Documentation](https://docs.python.org/3/)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Rich Terminal Library](https://rich.readthedocs.io/)
- [SQLite Database](https://sqlite.org/docs.html)

---

## 📋 Changelog

For detailed version history and changes, see the [CHANGELOG.md](CHANGELOG.md).

### Version 0.3.0 - Architecture Simplification (November 2025)

#### Major Changes
- **Unified Configuration System**: Centralized all configuration in [`backend/config.py`](../backend/config.py) with organized sections for better maintainability
- **Database Migration Consolidation**: Merged separate migration systems into a single [`MigrationManager`](../backend/repositories/migrations.py) that handles both core and extended functionality
- **Frontend Component Refactoring**: Broke down the 1,630-line [`UnifiedPage.tsx`](../frontend/src/pages/UnifiedPage.tsx) into 17 focused components with clear responsibilities
- **State Management Organization**: Reorganized 18 separate state variables into logical groups (UI, Chat, LessonSettings, Browse, Settings)

#### Removed Components
- **Unused Zustand Store**: Eliminated unused state management library for cleaner architecture
- **WebSocket Client**: Removed unused websocket client that was not being utilized

#### Benefits Achieved
- **87% reduction** in main component file size (1,630 → 205 lines)
- **Improved maintainability** through modular component architecture
- **Better type safety** with centralized TypeScript interfaces
- **Enhanced developer experience** with organized configuration sections
- **Simplified database management** with unified migration system

#### Breaking Changes
- None - backward compatibility has been maintained throughout the refactoring

#### Technical Details
- **Frontend**: Created 4 custom hooks ([`useChat.ts`](../frontend/src/hooks/useChat.ts), [`useSession.ts`](../frontend/src/hooks/useSession.ts), [`useImages.ts`](../frontend/src/hooks/useImages.ts), [`useResizing.ts`](../frontend/src/hooks/useResizing.ts))
- **Types**: Centralized all TypeScript interfaces in [`frontend/src/types/unified.ts`](../frontend/src/types/unified.ts)
- **Components**: Split into logical groups (Layout, Chat, View Modes, Modals)
- **Configuration**: Organized into 10 configuration classes with automatic validation

---

*This documentation is continuously updated. Last updated: November 2025*