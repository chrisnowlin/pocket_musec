# Web Search Integration Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Technical Details](#technical-details)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Overview

### What is Web Search Integration?

The Web Search Integration enhances PocketMusec's lesson planning capabilities by incorporating real-time web search results from educational resources. This feature integrates with the Brave Search API to provide teachers with current educational content, research, and teaching materials that complement the existing RAG (Retrieval-Augmented Generation) system.

### Why It Enhances Music Education

Web search integration provides several key benefits for music educators:

- **Current Content**: Access to the latest research, methodologies, and educational trends in music education
- **Diverse Resources**: Supplement locally stored standards with external expertise and perspectives  
- **Real-World Examples**: Find current examples, case studies, and teaching materials from educational institutions
- **Professional Development**: Continuously updated content helps teachers stay current with pedagogical advances

### Benefits Over RAG-Only Approach

While PocketMusec's RAG system provides excellent access to ingested standards and documents, web search integration adds:

- **Freshness**: Content from the past day ensures relevance and timeliness
- **Breadth**: Access to a wider range of educational perspectives and resources
- **Context**: Real-world examples and current implementations in music education
- **Complementarity**: Web results enhance rather than replace existing RAG content

## Architecture

### Integration with Existing RAG System

The web search service is designed to seamlessly complement the existing RAG architecture:

```
Lesson Generation Workflow:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  LessonAgent     │───▶│  Context Merge  │
│                 │    │                  │    │                 │
│ - Grade Level   │    │ - RAG Context    │    │ - Standards     │
│ - Topic         │    │ - Web Context    │    │ - Web Results  │
│ - Standards     │    │ - Images         │    │ - Images        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ WebSearchService │    │  LLM Generation  │
                       │                  │    │                 │
                       │ - Query Optimize │    │ - Enhanced       │
                       │ - Educational    │    │   Prompts        │
                       │   Filtering      │    │ - Web-Enhanced   │
                       │ - Relevance      │    │   Lessons        │
└─────────────────┘    │   Scoring        │    └─────────────────┘
│  Brave Search    │    └──────────────────┘            │
│  API Integration │              │                     ▼
│                  │              ▼              ┌─────────────────┐
└─────────────────┘    ┌──────────────────┐    │ Final Lesson    │
                       │  Cache Layer     │    │                 │
                       │                  │    │ - Standards     │
                       │ - LRU Cache      │    │ - Aligned       │
                       │ - TTL Management  │    │ - Web-Enhanced  │
                       └──────────────────┘    │ - Exportable    │
                                              └─────────────────┘
```

### Search Process Flow

1. **Query Analysis**: LessonAgent analyzes user query and educational context
2. **Query Optimization**: [`WebSearchService._build_educational_query()`](../backend/services/web_search_service.py:239) enhances the query with educational terms and domain filters
3. **API Execution**: Search is performed using Brave Search API with educational parameters
4. **Result Filtering**: Results are filtered for educational relevance and domain quality
5. **Relevance Scoring**: Each result is scored based on educational content indicators
6. **Context Integration**: High-quality results are formatted and integrated into lesson prompts

### Content Filtering and Relevance Scoring

The educational filtering system ensures high-quality, relevant results:

#### Domain Filtering
- **Educational Domains**: Priority given to `.edu`, `.org`, and `.gov` domains
- **Content Indicators**: Analysis of titles and snippets for educational keywords
- **Relevance Threshold**: Minimum score requirements filter out low-quality results

#### Scoring Algorithm
Results are scored using multiple factors:
- **Educational Domain Bonus**: +0.3 for .edu/.org/.gov domains
- **Keyword Matching**: Up to +0.4 for educational terms (teaching, curriculum, lesson, etc.)
- **Query Relevance**: Up to +0.3 for query term matching in content
- **Final Score**: Capped at 1.0 for normalization

### Caching Mechanism

Performance is optimized through intelligent caching:

- **In-Memory Cache**: LRU-style cache with configurable size limits
- **TTL Management**: Configurable time-to-live prevents stale content
- **Cache Keys**: MD5 hashes of query parameters ensure uniqueness
- **Eviction Strategy**: Oldest entries removed when cache reaches capacity

## Features

### Educational Content Discovery

The system excels at finding music education resources through:

- **Smart Query Enhancement**: Automatic addition of music education terms and grade-level context
- **Domain Prioritization**: Educational institutions given preference in results
- **Content Analysis**: Snippet and title analysis for educational value
- **Freshness Filtering**: Focus on recent content (past day) for current relevance

### Current Trends and Research Integration

Teachers benefit from access to:

- **Latest Research**: Current findings in music pedagogy and education
- **Teaching Methodologies**: Modern approaches and techniques
- **Curriculum Developments**: Recent changes and innovations in music education
- **Professional Resources**: Articles, studies, and professional development materials

### Domain Filtering

Configurable filtering ensures quality results:

- **Educational Domains**: Optional restriction to .edu/.org/.gov domains
- **Content-Based Filtering**: Analysis of content for educational indicators
- **Configurable Thresholds**: Adjustable relevance score minimums
- **Flexible Policies**: Can be relaxed or tightened based on needs

### Relevance Scoring

Sophisticated scoring provides the most useful results first:

- **Multi-Factor Scoring**: Combines domain, keyword, and query relevance
- **Educational Keywords**: Specialized vocabulary for music education
- **Context Awareness**: Grade level and subject consideration
- **Quality Ranking**: Results sorted by educational relevance

### Caching for Performance

Intelligent caching optimizes response times:

- **Configurable Cache Size**: Adjust based on memory constraints
- **TTL Management**: Automatic expiration of old content
- **Cache Statistics**: Monitor cache performance and hit rates
- **Manual Control**: Ability to clear cache when needed

## Configuration

### Getting Brave Search API Key

1. **Visit Brave Search API**: Navigate to [https://brave.com/search/api/](https://brave.com/search/api/)
2. **Create Account**: Register for a Brave Search API account
3. **Generate API Key**: Create a new API key for your application
4. **Configure Key**: Add the key to your environment configuration

### Environment Variable Setup

Add the following to your `.env` file:

```bash
# Required for Web Search
BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here

# Optional Web Search Configuration
BRAVE_SEARCH_CACHE_TTL=3600
BRAVE_SEARCH_MAX_CACHE_SIZE=100
BRAVE_SEARCH_TIMEOUT=30
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5
```

### Configuration Options

| Variable | Description | Default | Recommendations |
|----------|-------------|---------|-----------------|
| `BRAVE_SEARCH_API_KEY` | Brave Search API authentication key | Required | Keep secure, never commit to version control |
| `BRAVE_SEARCH_CACHE_TTL` | Cache time-to-live in seconds | 3600 (1 hour) | Increase for better performance, decrease for freshness |
| `BRAVE_SEARCH_MAX_CACHE_SIZE` | Maximum cached searches | 100 | Adjust based on available memory |
| `BRAVE_SEARCH_TIMEOUT` | API request timeout in seconds | 30 | Increase for slow networks, decrease for responsiveness |
| `BRAVE_SEARCH_EDUCATIONAL_ONLY` | Filter to educational domains only | true | Set to false for broader results |
| `BRAVE_SEARCH_MIN_RELEVANCE_SCORE` | Minimum relevance threshold | 0.5 | Lower for more results, higher for quality focus |

### Testing the Integration

Use the provided test scripts to verify your configuration:

```bash
# Test basic web search functionality
uv run python test_web_search_simple.py

# Test full integration with lesson agent
uv run python test_web_search_integration.py
```

## Usage

### For Teachers: Web-Enhanced Lesson Planning

Teachers can benefit from web-enhanced lessons through:

1. **Richer Content**: Lessons include current research and examples
2. **Diverse Perspectives**: Multiple educational sources and viewpoints
3. **Professional Resources**: Access to teaching methodologies and materials
4. **Stay Current**: Regular updates on music education trends

### Lesson Generation with Web Search

When generating lessons, the system automatically:

- **Analyzes Context**: Determines when web search would be beneficial
- **Optimizes Queries**: Enhances search terms for educational content
- **Filters Results**: Ensures only high-quality, educational content is included
- **Integrates Content**: Seamlessly weaves web results into lesson plans

### Example: Before/After Comparison

#### Before Web Search (RAG Only)
```
Lesson: Introduction to Rhythm for Grade 3

Objectives:
- Understand basic rhythm concepts
- Identify quarter notes and eighth notes
- Clap simple rhythm patterns

Standards: 3.M.R.1, 3.M.R.2
```

#### After Web Search (Enhanced)
```
Lesson: Introduction to Rhythm for Grade 3

Objectives:
- Understand basic rhythm concepts using current methodologies
- Identify quarter notes and eighth notes with visual aids
- Clap simple rhythm patterns from contemporary examples
- Explore cultural rhythm traditions (recent research from Berklee College)

Standards: 3.M.R.1, 3.M.R.2

Web-Enhanced Resources:
- Current research on rhythm pedagogy in elementary education
- Interactive rhythm examples from music education institutions
- Cross-cultural rhythm activities for diverse classrooms
```

### Teacher Benefits

- **Professional Growth**: Access to current research and methodologies
- **Student Engagement**: Fresh, relevant examples and activities
- **Time Savings**: Curated educational resources without manual searching
- **Quality Assurance**: Pre-filtered, educationally appropriate content

## Technical Details

### WebSearchService Architecture

The [`WebSearchService`](../backend/services/web_search_service.py:100) class provides the core functionality:

#### Key Components

- **SearchResult**: Individual result with educational metadata and scoring
- **WebSearchContext**: Container for search results and timing information
- **CacheEntry**: Cached result with TTL validation
- **WebSearchService**: Main service class with async operations

#### Core Methods

- [`search_educational_resources()`](../backend/services/web_search_service.py:153): Main search method with optimization
- [`_build_educational_query()`](../backend/services/web_search_service.py:239): Query enhancement for educational content
- [`_filter_educational_results()`](../backend/services/web_search_service.py:278): Content filtering and quality control
- [`_score_educational_relevance()`](../backend/services/web_search_service.py:323): Multi-factor relevance scoring

### Integration Points in LessonAgent

The [`LessonAgent`](../backend/pocketflow/lesson_agent.py) integrates web search through several key points:

#### Initialization (Lines 28-51)
```python
# Web search service initialization
self.web_search_service = WebSearchService(
    api_key=config.web_search.api_key,
    cache_ttl=config.web_search.cache_ttl,
    educational_only=config.web_search.educational_only
)
```

#### Context Retrieval (Lines 426-483)
```python
async def _get_web_search_context(self, query: str, grade_level: str = None) -> Optional[str]:
    """Retrieve web search context for lesson generation"""
    context = await self.web_search_service.search_educational_resources(
        query=query,
        max_results=5,
        grade_level=grade_level,
        subject="music"
    )
    return self._format_web_search_context(context) if context else None
```

#### Context Integration
Web search context is combined with RAG context in [`_build_lesson_context_from_conversation()`](../backend/pocketflow/lesson_agent.py):

```python
# Combine RAG and web search contexts
enhanced_context = rag_context
if web_search_context:
    enhanced_context += f"\n\n{web_search_context}"
```

### Prompt Template Enhancements

The [`LessonPromptContext`](../backend/llm/prompt_templates.py:25) dataclass includes web search integration:

```python
@dataclass
class LessonPromptContext:
    # ... existing fields ...
    web_search_context: Optional[str] = None
```

The [`_format_web_search_context()`](../backend/llm/prompt_templates.py:72) method formats web results:

```python
def _format_web_search_context(self, context: WebSearchContext) -> str:
    """Format web search context for prompt inclusion"""
    if not context or not context.results:
        return ""
    
    formatted_results = []
    for result in context.results[:3]:  # Top 3 results
        formatted_results.append(
            f"Title: {result.title}\n"
            f"Source: {result.domain}\n"
            f"Content: {result.snippet}\n"
            f"Relevance: {result.relevance_score:.2f}"
        )
    
    return (
        f"\n\n<web_search_results>\n"
        f"Query: {context.query}\n"
        f"Results: {len(context.results)} educational resources\n\n"
        f"{'-' * 50}\n"
        f"{'\n\n'.join(formatted_results)}"
        f"\n{'-' * 50}\n"
        f"</web_search_results>"
    )
```

### Error Handling and Fallbacks

The system includes comprehensive error handling:

#### API Failures
- **Automatic Retries**: Exponential backoff for network issues
- **Graceful Degradation**: Lessons continue without web content on failures
- **Error Logging**: Detailed logging for troubleshooting
- **Fallback Mechanisms**: RAG-only operation when web search unavailable

#### Cache Issues
- **Cache Bypass**: Direct API calls when cache fails
- **Memory Management**: Automatic cleanup of corrupted entries
- **Performance Monitoring**: Cache hit/miss statistics

#### Content Quality
- **Minimum Thresholds**: Configurable relevance score floors
- **Content Validation**: Verification of educational value
- **Safety Filtering**: Moderate safe search settings enabled

## Troubleshooting

### Common Setup Issues

#### API Key Problems

**Problem**: "Brave Search API key not configured" error

**Solution**:
1. Verify `BRAVE_SEARCH_API_KEY` is set in `.env` file
2. Check API key validity with Brave Search dashboard
3. Ensure no extra spaces or special characters in key
4. Restart application after adding key

**Test**:
```bash
echo $BRAVE_SEARCH_API_KEY  # Should display your key
```

#### Network Connectivity

**Problem**: Search timeouts or connection failures

**Solutions**:
- **Increase Timeout**: Set `BRAVE_SEARCH_TIMEOUT=60` in `.env`
- **Check Firewall**: Ensure port 443 HTTPS access to api.search.brave.com
- **Verify DNS**: Test with `nslookup api.search.brave.com`
- **Proxy Configuration**: Configure proxy settings if required

**Test**:
```bash
curl -I https://api.search.brave.com/res/v1/web/search
```

### Performance Optimization

#### Slow Search Responses

**Causes and Solutions**:
- **Cache Misses**: Increase `BRAVE_SEARCH_CACHE_TTL` to 7200 (2 hours)
- **Large Result Sets**: Reduce `max_results` parameter in search calls
- **Network Latency**: Consider CDN or regional API endpoints
- **Memory Constraints**: Monitor cache usage with `get_cache_stats()`

**Monitoring**:
```python
# Check cache performance
stats = web_search_service.get_cache_stats()
print(f"Cache hit rate: {stats['cache_size']}/{stats['max_cache_size']}")
```

#### High Memory Usage

**Solutions**:
- **Reduce Cache Size**: Set `BRAVE_SEARCH_MAX_CACHE_SIZE=50`
- **Shorten TTL**: Set `BRAVE_SEARCH_CACHE_TTL=1800` (30 minutes)
- **Monitor Memory**: Use system monitoring tools
- **Clear Cache**: Call `clear_cache()` method periodically

### API Rate Limit Handling

#### Rate Limit Errors

**Symptoms**: HTTP 429 responses, search failures

**Solutions**:
- **Implement Backoff**: System includes automatic exponential backoff
- **Reduce Frequency**: Cache more aggressively with longer TTL
- **Batch Requests**: Combine multiple queries when possible
- **Upgrade Plan**: Consider higher-tier API plan for increased limits

**Monitoring**:
```python
# Check search frequency in logs
grep "Search completed" logs/pocketmusec.log | wc -l
```

### Debugging Tips

#### Enable Debug Logging

```bash
# Set debug level in .env
LOG_LEVEL=DEBUG

# Or temporarily enable
export LOG_LEVEL=DEBUG
```

#### Manual API Testing

```python
# Test API directly
import asyncio
from backend.services.web_search_service import WebSearchService

async def test_search():
    service = WebSearchService()
    result = await service.search_educational_resources(
        "music theory lesson plans",
        max_results=3
    )
    print(f"Found {len(result.results)} results")

asyncio.run(test_search())
```

#### Cache Inspection

```python
# Monitor cache behavior
stats = web_search_service.get_cache_stats()
print(f"Cache stats: {stats}")

# Clear cache if needed
await web_search_service.clear_cache()
```

## Best Practices

### Query Optimization

#### Effective Search Queries

- **Be Specific**: Use detailed queries like "grade 3 rhythm activities" instead of "music"
- **Include Context**: Add grade level, subject, and specific topics
- **Educational Terms**: Include "lesson plan", "teaching", "curriculum" when appropriate
- **Avoid Jargon**: Use clear, searchable terms rather than technical jargon

#### Examples

**Good Queries**:
- "elementary music composition activities"
- "teaching music notation to beginners"
- "grade 5 music assessment strategies"

**Less Effective Queries**:
- "music"
- "songs"
- "beethoven symphony analysis" (too advanced for K-12)

### Content Evaluation

#### Quality Indicators

Look for these signs in search results:
- **Educational Domains**: .edu, .org, .gov
- **Professional Sources**: Music education associations, universities
- **Current Content**: Recent publication dates, current methodologies
- **Teaching Focus**: Content specifically for educators
- **Age Appropriate**: Content suitable for target grade level

#### Red Flags

- **Commercial Sites**: Sites selling products rather than educational content
- **Outdated Information**: Older than 5 years, unless foundational research
- **Non-Educational**: General content not tailored for teaching
- **Low Relevance**: Scores below 0.5 may not be educationally useful

### Balancing Web and RAG Content

#### Optimal Integration Strategy

- **RAG Foundation**: Use RAG for standards, core concepts, and curriculum requirements
- **Web Enhancement**: Add web content for current research, examples, and methodologies
- **Context Awareness**: Let the system determine when web search adds value
- **Quality Control**: Maintain high relevance thresholds for web content

#### Proportion Guidelines

- **Core Content**: 70-80% from RAG (standards, curriculum, local materials)
- **Enhancement Content**: 20-30% from web search (current research, examples)
- **Adjust as Needed**: Modify based on specific lesson requirements

### Privacy Considerations

#### Data Protection

- **No Personal Data**: Web search queries contain only lesson planning information
- **Educational Focus**: Queries limited to educational content, reducing privacy concerns
- **API Security**: API keys stored securely, not exposed in logs
- **Content Filtering**: Moderate safe search prevents inappropriate content

#### Best Practices

- **Review Content**: Always review web search results before including in lessons
- **Source Verification**: Check credibility of external sources
- **Age Appropriateness**: Ensure content is suitable for student age group
- **Copyright Compliance**: Respect copyright when using external resources

### Performance Tuning

#### Cache Optimization

- **Monitor Hit Rate**: Aim for >70% cache hit rate for frequently used queries
- **Adjust TTL**: Balance freshness and performance based on usage patterns
- **Memory Management**: Monitor cache size relative to available memory
- **Regular Cleanup**: Clear cache periodically to remove stale entries

#### Network Optimization

- **Connection Pooling**: Use persistent connections for API calls
- **Timeout Configuration**: Set appropriate timeouts for your network conditions
- **Retry Logic**: Implement exponential backoff for failed requests
- **Monitoring**: Track API response times and success rates

### Integration Testing

#### Test Scenarios

Regularly test web search integration with these scenarios:
- **Standard Queries**: Common music education topics
- **Grade-Specific Content**: Different educational levels
- **Edge Cases**: Unusual or very specific queries
- **Error Conditions**: Network failures, API limits, invalid keys

#### Monitoring Metrics

Track these key metrics:
- **Search Success Rate**: Percentage of successful searches
- **Response Time**: Average search completion time
- **Cache Performance**: Hit/miss ratios and TTL effectiveness
- **Content Quality**: Average relevance scores of returned results

---

This documentation provides comprehensive coverage of PocketMusec's web search integration. For additional information, see:

- [Configuration Guide](WEB_SEARCH_CONFIGURATION.md) for detailed setup instructions
- [API Documentation](API.md) for technical integration details
- [Developer Setup Guide](DEVELOPER_SETUP.md) for development environment configuration
- [User Guide](USER_GUIDE.md) for teacher-facing usage instructions

For technical support or to report issues, please refer to the [main project documentation](README.md).