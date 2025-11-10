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

### For System Administrators
- **[Installation & Deployment](DEVELOPER_SETUP.md#deployment-and-distribution)** - System setup requirements
- **[Configuration](DEVELOPER_SETUP.md#environment-configuration)** - Environment variables and settings
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

### 2. Import NC Music Standards
```bash
pocketmusec ingest standards "NC Music Standards.pdf"
```

### 3. Generate Your First Lesson
```bash
pocketmusec generate lesson
```

That's it! You're ready to create standards-aligned music lessons.

---

## 🎵 For Music Teachers

### What PocketMusec Does
- ✅ **Saves Time** - Generate complete lesson plans in minutes
- ✅ **Standards Aligned** - Automatically matches NC music standards  
- ✅ **Grade Specific** - Content tailored for K-12 music education
- ✅ **Four Music Strands** - Covers Creating, Performing, Responding, and Critical Response
- ✅ **Editable** - Customize lessons in your favorite editor
- ✅ **Organized** - Keeps track of all your lesson drafts

### Key Features
- **Interactive Lesson Generation** - Conversational interface guides you through each step
- **Standards-Based** - All lessons aligned with North Carolina music education standards
- **Smart Search** - Find standards using natural language queries
- **Draft History** - Track changes and maintain version history
- **Editor Integration** - Works with your default text editor

### Getting Started
1. **Read the [Teacher Guide](TEACHER_GUIDE.md)** for detailed instructions
2. **Import your standards** using the ingest command
3. **Start generating lessons** with the interactive CLI
4. **Customize and save** lessons for your classroom

---

## 💻 For Developers

### Architecture Overview
```
pocket_musec/
├── backend/                 # Core application logic
│   ├── ingestion/          # PDF parsing and standards ingestion
│   ├── llm/               # AI/LLM integration (Chutes API)
│   ├── pocketflow/        # Conversation flow framework
│   ├── repositories/      # Database layer (SQLite)
│   └── utils/             # Utility functions
├── cli/                   # Command-line interface (Typer)
│   ├── commands/         # CLI command implementations
│   └── main.py          # CLI entry point
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation
└── data/                 # SQLite database and files
```

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

## 📋 CLI Commands Reference

### Main Commands
```bash
# Show help
pocketmusec --help

# Ingest NC music standards
pocketmusec ingest standards "standards.pdf"

# Generate interactive lesson
pocketmusec generate lesson

# Manage embeddings for smart search
pocketmusec embeddings generate
pocketmusec embeddings search "rhythm activities"
pocketmusec embeddings stats
```

### Advanced Usage
```bash
# Custom database location
pocketmusec ingest standards "standards.pdf" --db-path "/custom/path.db"

# Save lesson directly to file
pocketmusec generate lesson --output "my_lesson.md"

# Search with filters
pocketmusec embeddings search "composition" --grade "8th Grade" --strand "CN"

# Force regeneration
pocketmusec embeddings generate --force

# Review prepared texts for debugging
pocketmusec embeddings texts
pocketmusec embeddings show-text 2.CN.1 --type standard
```

See the [CLI Commands Documentation](CLI_COMMANDS.md) for complete reference.

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

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

### File Locations
- **Database:** `./data/standards.db` (created automatically)
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
```bash
# Morning: Generate today's lesson
pocketmusec generate lesson
# Follow prompts for grade, strand, standard
# Edit and save for your classes

# Afternoon: Plan tomorrow's lesson
pocketmusec generate lesson --output "tomorrow_lesson.md"
# Use different standard or strand

# End of day: Review and organize
# Your lessons are saved with metadata and standards alignment
```

### Unit Planning
```bash
# Search for related standards
pocketmusec embeddings search "rhythm fundamentals" --grade "3rd Grade"

# Generate series of lessons
for strand in "CN" "PR" "RE"; do
    pocketmusec generate lesson --output "unit_${strand}_lesson.md"
done

# Create unit overview from generated lessons
# Edit and combine as needed
```

### Curriculum Mapping
```bash
# Ingest standards (if not already done)
pocketmusec ingest standards "NC Music Standards.pdf"

# Generate embeddings for search
pocketmusec embeddings generate

# Search curriculum topics
pocketmusec embeddings search "music notation" --limit 20
pocketmusec embeddings search "ensemble skills" --grade "High School"

# Review prepared texts for quality assurance
pocketmusec embeddings texts
```

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
ls -la data/standards.db

# Recreate database if corrupted
rm data/standards.db
pocketmusec ingest standards "NC Music Standards.pdf"
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
2. **Batch lesson generation** - Plan multiple lessons at once
3. **Local database** - Standards cached locally for fast access
4. **Optimize batch size** - Adjust `--batch-size` for your system

### System Optimization
```bash
# Increase batch size for faster embedding generation
pocketmusec embeddings generate --batch-size 20

# Use custom database on faster storage
pocketmusec ingest standards "standards.pdf" --db-path "/ssd/standards.db"

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

*This documentation is continuously updated. Last updated: November 2025*