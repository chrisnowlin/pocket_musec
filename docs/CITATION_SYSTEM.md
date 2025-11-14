# Citation System Implementation Guide

## Overview

The PocketMusec citation system automatically tracks and cites web search sources used during lesson generation. This ensures educational content is properly attributed and provides teachers with verifiable resources.

## Features

### Automatic Citation Integration
- **Web Search Tracking**: All web search results are automatically tracked during lesson generation
- **Inline Citations**: Sources are cited inline using `[Web Source: URL]` format or numbered citations `[1]`, `[2]`, etc.
- **Bibliography Generation**: Comprehensive citations section is automatically included in generated lessons
- **Clickable URLs**: Frontend renders citation URLs as clickable hyperlinks that open in new tabs

### Citation Format
The system uses footnote-style citations with clear source attribution:

**Inline Citation Examples:**
- `[Web Source: https://www.teachingmusic.org/rhythm]`
- `[Web Source: www.musictech.com/tools]`
- `[1]`, `[2]`, `[3]` (numbered format)

**Bibliography Section:**
```markdown
## Citations

1. [Web Source: https://www.teachingmusic.org/rhythm] - Comprehensive guide for teaching rhythm patterns
2. [Web Source: www.musictech.com/tools] - Interactive tools for rhythm composition  
3. [Web Source: https://musiceducation.org/research] - Research-based pedagogy for music education
```

## Implementation Details

### Backend Components

#### 1. Web Search Service (`backend/services/web_search_service.py`)
- Handles educational web searches via Brave Search API
- Filters results for educational relevance
- Assigns citation IDs and formats search results
- Generates bibliography from search context

#### 2. Lesson Agent (`backend/pocketflow/lesson_agent.py`)
- Integrates web search context into lesson generation
- Appends bibliography to generated lessons
- Provides fallback citation generation methods
- Ensures proper citation formatting

#### 3. Prompt Templates (`backend/llm/prompt_templates.py`)
- Enhanced with explicit citation requirements
- Includes MUST-level instructions for footnote citations
- Provides structured guidance for citation placement
- Mandates bibliography section inclusion

### Frontend Components

#### Markdown Renderer (`frontend/src/components/MarkdownRenderer.tsx`)
- Renders citation URLs as clickable hyperlinks
- Opens links in new tabs for user convenience
- Maintains proper markdown formatting
- Handles both full URLs and www. prefixes

## Configuration

### Environment Variables
```bash
# Web Search Configuration
BRAVE_SEARCH_API_KEY=your_api_key_here
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5

# Citation Configuration  
CITATION_AUTO_INCLUDE=true
CITATION_FORMAT=footnote
```

### Citation Behavior
- **Automatic**: Citations are automatically included when web search content is used
- **Mandatory**: System requires citations for web source references
- **Structured**: Consistent format across all generated lessons
- **User-Friendly**: Clickable URLs in frontend interface

## Usage Examples

### Lesson Generation with Citations
When a teacher requests a lesson on "teaching rhythm patterns to 3rd graders":

1. **Web Search**: System finds relevant educational resources
2. **Content Generation**: Lesson incorporates web search insights
3. **Citation Integration**: Sources are cited inline and in bibliography
4. **Frontend Display**: URLs render as clickable links

### Generated Lesson Example
```markdown
## Learning Objectives
- Students will perform rhythm patterns using quarter and eighth notes [Web Source: https://www.teachingmusic.org/rhythm]
- Students will create their own rhythm compositions [Web Source: www.musictech.com/tools]

## Lesson Activities
1. **Rhythm Warm-up** (5 minutes)
   - Clap and count rhythm patterns
   - Use body percussion to reinforce concepts [Web Source: https://musiceducation.org/research]

## Citations
1. [Web Source: https://www.teachingmusic.org/rhythm] - Comprehensive guide for teaching rhythm patterns
2. [Web Source: www.musictech.com/tools] - Interactive tools for rhythm composition
3. [Web Source: https://musiceducation.org/research] - Research-based pedagogy for music education
```

## Testing and Validation

### Test Coverage
- **Unit Tests**: Citation formatting and bibliography generation
- **Integration Tests**: End-to-end lesson generation with citations
- **Frontend Tests**: URL rendering and click behavior
- **API Tests**: Citation inclusion in lesson responses

### Validation Results
- ✅ Citation system fully operational
- ✅ Web search integration working correctly
- ✅ Lesson generation with citations functional
- ✅ Frontend URL rendering compatible
- ✅ Ready for production deployment

## Benefits

### For Teachers
- **Resource Verification**: Easy access to source materials
- **Professional Development**: Discover new educational resources
- **Lesson Enhancement**: Current, web-enhanced content
- **Credibility**: Proper attribution builds trust

### For Students
- **Extended Learning**: Access to additional resources
- **Research Skills**: Learn proper citation practices
- **Current Content**: Up-to-date educational approaches

### For the System
- **Content Quality**: Web-enhanced lessons with proper attribution
- **User Trust**: Transparent source tracking
- **Educational Value**: Integration of current research and practices

## Future Enhancements

### Planned Features
- **Citation Export**: Download bibliography as separate file
- **Source Filtering**: Option to include/exclude certain types of sources
- **Citation Styles**: Support for different citation formats (APA, MLA, etc.)
- **Source Analytics**: Track which resources are most useful

### Integration Opportunities
- **Library Systems**: Connect to academic databases
- **Educational Platforms**: Integration with established resource repositories
- **Professional Development**: Curated collections of high-quality sources

## Troubleshooting

### Common Issues
- **Missing Citations**: Check web search configuration and API keys
- **Broken Links**: Verify URL formatting in web search results
- **Display Issues**: Ensure frontend MarkdownRenderer is properly configured

### Debugging Tools
- Citation system test scripts in `/test_citation_system_*.py`
- Web search service logs and error handling
- Frontend browser console for URL rendering issues

## Conclusion

The PocketMusec citation system provides comprehensive, automatic citation integration for lesson generation. It ensures educational content is properly attributed while maintaining user-friendly access to source materials. The system is production-ready and enhances the overall quality and credibility of generated lesson plans.