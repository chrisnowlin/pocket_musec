
# Web Search Configuration Quick Reference

Complete configuration guide for PocketMusec's web search integration with Brave Search API.

Complete configuration guide for PocketMusec's web search integration with Brave Search API.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Example Configuration](#example-configuration)
3. [Performance Tuning](#performance-tuning)
4. [Troubleshooting](#troubleshooting)
5. [Security Considerations](#security-considerations)

## Environment Variables

### Required Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BRAVE_SEARCH_API_KEY` | string | **Required** | Brave Search API authentication key |

**Getting Your API Key:**
1. Visit [https://brave.com/search/api/](https://brave.com/search/api/)
2. Create a Brave Search API account
3. Generate a new API key
4. Add to your `.env` file

### Optional Variables

| Variable | Type | Default | Recommended Range | Description |
|----------|------|---------|-------------------|-------------|
| `BRAVE_SEARCH_CACHE_TTL` | integer | 3600 | 1800-7200 | Cache time-to-live in seconds |
| `BRAVE_SEARCH_MAX_CACHE_SIZE` | integer | 100 | 50-200 | Maximum number of cached searches |
| `BRAVE_SEARCH_TIMEOUT` | integer | 30 | 15-60 | API request timeout in seconds |
| `BRAVE_SEARCH_EDUCATIONAL_ONLY` | boolean | true | true/false | Filter to educational domains only |
| `BRAVE_SEARCH_MIN_RELEVANCE_SCORE` | float | 0.5 | 0.3-0.7 | Minimum relevance score threshold |

### Variable Details

#### BRAVE_SEARCH_CACHE_TTL
- **Purpose**: How long search results are cached before refresh
- **Lower values** (1800s = 30min): Fresher content, more API calls
- **Higher values** (7200s = 2hrs): Fewer API calls, potentially stale content
- **Recommended**: 3600s (1 hour) for most use cases

#### BRAVE_SEARCH_MAX_CACHE_SIZE
- **Purpose**: Maximum number of searches kept in memory cache
- **Memory usage**: Approximately 1KB per cached search
- **Lower values** (50): Less memory usage, more cache misses
- **Higher values** (200): More memory usage, better cache performance
- **Recommended**: 100 for balanced performance

#### BRAVE_SEARCH_TIMEOUT
- **Purpose**: Maximum wait time for Brave Search API responses
- **Network considerations**: Increase for slow/unreliable connections
- **Performance**: Decrease for faster failure detection
- **Recommended**: 30 seconds for most networks

#### BRAVE_SEARCH_EDUCATIONAL_ONLY
- **Purpose**: Restrict searches to educational domains (.edu, .org, .gov)
- **true**: Higher quality results, limited scope
- **false**: Broader results, may include non-educational content
- **Recommended**: true for educational use cases

#### BRAVE_SEARCH_MIN_RELEVANCE_SCORE
- **Purpose**: Filter out low-quality search results
- **Range**: 0.0 (all results) to 1.0 (only perfect matches)
- **Lower values** (0.3): More results, lower quality
- **Higher values** (0.7): Fewer results, higher quality
- **Recommended**: 0.5 for balanced quality/quantity

## Example Configuration

### Basic Setup (.env)

```bash
# Required: Brave Search API Key
BRAVE_SEARCH_API_KEY=your_brave_search_api_key_here

# Optional: Use defaults for most cases
# The following will use default values if not specified
```

### Development Environment

```bash
# Development configuration - more verbose, faster refresh
BRAVE_SEARCH_API_KEY=dev_brave_search_api_key
BRAVE_SEARCH_CACHE_TTL=1800
BRAVE_SEARCH_MAX_CACHE_SIZE=50
BRAVE_SEARCH_TIMEOUT=15
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.4
```

### Production Environment

```bash
# Production configuration - optimized for performance
BRAVE_SEARCH_API_KEY=prod_brave_search_api_key
BRAVE_SEARCH_CACHE_TTL=7200
BRAVE_SEARCH_MAX_CACHE_SIZE=150
BRAVE_SEARCH_TIMEOUT=30
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.6
```

### High-Traffic Environment

```bash
# High-traffic configuration - aggressive caching
BRAVE_SEARCH_API_KEY=high_traffic_api_key
BRAVE_SEARCH_CACHE_TTL=14400
BRAVE_SEARCH_MAX_CACHE_SIZE=200
BRAVE_SEARCH_TIMEOUT=45
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5
```

### Research-Oriented Setup

```bash
# Research configuration - broader scope
BRAVE_SEARCH_API_KEY=research_api_key
BRAVE_SEARCH_CACHE_TTL=3600
BRAVE_SEARCH_MAX_CACHE_SIZE=100
BRAVE_SEARCH_TIMEOUT=60
BRAVE_SEARCH_EDUCATIONAL_ONLY=false
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.3
```

## Performance Tuning

### Cache Optimization Strategies

#### High Performance Scenario
**Goal**: Minimize API calls, maximize response speed

```bash
BRAVE_SEARCH_CACHE_TTL=14400      # 4 hours
BRAVE_SEARCH_MAX_CACHE_SIZE=200   # Large cache
BRAVE_SEARCH_TIMEOUT=45           # Generous timeout
```

**Trade-offs**: Less fresh content, higher memory usage

#### Fresh Content Scenario
**Goal**: Always get the latest educational content

```bash
BRAVE_SEARCH_CACHE_TTL=900        # 15 minutes
BRAVE_SEARCH_MAX_CACHE_SIZE=25    # Small cache
BRAVE_SEARCH_TIMEOUT=15           # Quick failure
```

**Trade-offs**: More API calls, potentially higher costs

#### Balanced Scenario
**Goal**: Good balance between freshness and performance

```bash
BRAVE_SEARCH_CACHE_TTL=3600       # 1 hour (default)
BRAVE_SEARCH_MAX_CACHE_SIZE=100   # Moderate cache
BRAVE_SEARCH_TIMEOUT=30           # Standard timeout
```

### Quality vs. Quantity Tuning

#### High Quality Results
**Use Case**: Professional development, research

```bash
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.7
```

#### Comprehensive Results
**Use Case**: Exploratory lesson planning, diverse sources

```bash
BRAVE_SEARCH_EDUCATIONAL_ONLY=false
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.3
```

#### Standard Educational Use
**Use Case**: Daily lesson planning, classroom use

```bash
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5
```

### Network Optimization

#### Reliable High-Speed Network
```bash
BRAVE_SEARCH_TIMEOUT=15
BRAVE_SEARCH_CACHE_TTL=1800
```

#### Unreliable or Slow Network
```bash
BRAVE_SEARCH_TIMEOUT=60
BRAVE_SEARCH_CACHE_TTL=7200
```

#### Metered or Expensive API Usage
```bash
BRAVE_SEARCH_TIMEOUT=30
BRAVE_SEARCH_CACHE_TTL=14400
BRAVE_SEARCH_MAX_CACHE_SIZE=200
```

### Memory Management

#### Limited Memory Resources (< 2GB available)
```bash
BRAVE_SEARCH_MAX_CACHE_SIZE=25
BRAVE_SEARCH_CACHE_TTL=1800
```

#### Ample Memory Resources (> 4GB available)
```bash
BRAVE_SEARCH_MAX_CACHE_SIZE=200
BRAVE_SEARCH_CACHE_TTL=7200
```

## Troubleshooting

### Common Configuration Issues

#### API Key Problems
**Symptoms**: "Brave Search API key not configured" errors

**Solutions**:
1. Verify `BRAVE_SEARCH_API_KEY` is set in `.env`
2. Check key validity at [Brave Search Dashboard](https://brave.com/search/api/)
3. Ensure no extra spaces or special characters
4. Restart application after changing key

**Test Command**:
```bash
echo $BRAVE_SEARCH_API_KEY  # Should display your key
```

#### Performance Issues
**Symptoms**: Slow lesson generation, timeouts

**Diagnostic Steps**:
1. Check network connectivity: `ping api.search.brave.com`
2. Test API directly:
   ```bash
   curl -H "X-Subscription-Token: $BRAVE_SEARCH_API_KEY" \
        "https://api.search.brave.com/res/v1/web/search?q=test&count=1"
   ```
3. Monitor cache performance with web search status endpoint

**Configuration Adjustments**:
- Increase `BRAVE_SEARCH_TIMEOUT` for slow networks
- Increase `BRAVE_SEARCH_CACHE_TTL` for better performance
- Decrease `BRAVE_SEARCH_MAX_CACHE_SIZE` if memory constrained

#### Quality Issues
**Symptoms**: Irrelevant or poor-quality search results

**Solutions**:
1. Increase `BRAVE_SEARCH_MIN_RELEVANCE_SCORE` to 0.6-0.7
2. Ensure `BRAVE_SEARCH_EDUCATIONAL_ONLY=true`
3. Check query terms for educational relevance
4. Review web search integration logs

#### Cache Issues
**Symptoms**: Inconsistent results, memory problems

**Solutions**:
1. Clear cache: `DELETE /web-search/cache` (API endpoint)
2. Reduce `BRAVE_SEARCH_MAX_CACHE_SIZE`
3. Decrease `BRAVE_SEARCH_CACHE_TTL`
4. Monitor cache statistics regularly

### Performance Monitoring

#### Cache Hit Rate Monitoring
```python
# Check cache statistics
stats = web_search_service.get_cache_stats()
hit_rate = stats['cache_size'] / stats['max_cache_size']
print(f"Cache utilization: {hit_rate:.2%}")
```

#### Response Time Tracking
```python
# Monitor search performance
import time

start_time = time.time()
result = await web_search_service.search_educational_resources("test query")
search_time = time.time() - start_time

print(f"Search completed in {search_time:.2f}s")
```

#### Usage Analytics
Regular monitoring points:
- Cache hit rate: Target >70%
- Average response time: Target <2 seconds
- API call frequency: Monitor for cost optimization
- Error rates: Target <5% failure rate

## Security Considerations

### API Key Protection

#### Never Commit API Keys
```bash
# Add to .gitignore
.env
.env.local
.env.production
```

#### Use Environment-Specific Keys
```bash
# Development
BRAVE_SEARCH_API_KEY=dev_key_with_limited_quota

# Production  
BRAVE_SEARCH_API_KEY=prod_key_with_higher_quota
```

#### Rotate Keys Regularly
1. Generate new API key every 90 days
2. Update configuration files
3. Revoke old keys in Brave Search dashboard
4. Monitor for any unauthorized usage

### Content Security

#### Educational Filtering
- Always keep `BRAVE_SEARCH_EDUCATIONAL_ONLY=true` for educational environments
- Monitor search results for inappropriate content
- Implement additional content filtering if needed

#### Query Logging
- Be aware of search query logging policies
- Avoid including sensitive personal information in searches
- Consider privacy implications for student data

### Network Security

#### HTTPS Only
- Brave Search API requires HTTPS connections
- Ensure firewall allows outbound HTTPS on port 443
- Configure proxy settings if required for your network

#### Rate Limiting
- Monitor API usage to avoid rate limits
- Implement client-side rate limiting if needed
- Use caching to reduce API call frequency

## Configuration Validation

### Startup Validation
The application validates web search configuration on startup:

```bash
# Check logs for validation messages
INFO: Web search service initialized
INFO: API key configured: true
INFO: Educational filtering: enabled
INFO: Cache size: 100 entries, TTL: 3600s
```

### Testing Configuration
Use the built-in test scripts to verify your setup:

```bash
# Test basic web search functionality
uv run python test_web_search_simple.py

# Test full integration with lesson agent
uv run python test_web_search_integration.py
```

### Expected Test Output
```
✓ Web search service initialized successfully
✓ API key validation passed
✓ Educational content filtering working
✓ Cache mechanism operational
✓ Integration with lesson agent functional
```

## Environment-Specific Configurations

### Development Configuration
Use for development and testing environments:

```bash
# .env.development
BRAVE_SEARCH_API_KEY=dev_api_key
BRAVE_SEARCH_CACHE_TTL=1800      # 30 minutes - fresher content
BRAVE_SEARCH_MAX_CACHE_SIZE=50   # Smaller cache - less memory
BRAVE_SEARCH_TIMEOUT=15          # Faster failure detection
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.4  # More results for testing
```

### Staging Configuration
Use for staging and pre-production testing:

```bash
# .env.staging
BRAVE_SEARCH_API_KEY=staging_api_key
BRAVE_SEARCH_CACHE_TTL=3600      # 1 hour - balanced
BRAVE_SEARCH_MAX_CACHE_SIZE=100  # Standard cache size
BRAVE_SEARCH_TIMEOUT=30          # Standard timeout
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.5  # Standard quality
```

### Production Configuration
Use for production deployment:

```bash
# .env.production
BRAVE_SEARCH_API_KEY=prod_api_key
BRAVE_SEARCH_CACHE_TTL=7200      # 2 hours - performance optimized
BRAVE_SEARCH_MAX_CACHE_SIZE=150  # Larger cache for high usage
BRAVE_SEARCH_TIMEOUT=45          # Conservative timeout
BRAVE_SEARCH_EDUCATIONAL_ONLY=true
BRAVE_SEARCH_MIN_RELEVANCE_SCORE=0.6  # Higher quality for production
```

## Migration Guide

### Upgrading from Previous Versions

If upgrading from a version without web search:

1. **Add API Key**: Obtain and configure Brave Search API key
2. **Update Configuration**: Add new environment variables to `.env`
3. **Test Integration**: Run test scripts to verify functionality
4. **Update Documentation**: Inform users about new web search features

### Migration Checklist

- [ ] Obtain Brave Search API key
- [ ] Add environment variables to configuration
- [ ] Test web search functionality
- [ ] Update user documentation
- [ ] Monitor performance after deployment
- [ ] Train staff on new features

## Quick Reference Commands

### Configuration Testing
```bash
# Test API connectivity
curl -H "X-Subscription-Token: $BRAVE_SEARCH_API_KEY" \
     "https://api.search.brave.com/res/v1/web/search?q=music+education&count=1"

# Check configuration in Python
python -c "from backend.config import config; print(config.web_search)"

# Run integration tests
uv run python test_web_search_integration.py
```

### Performance Monitoring
```bash
# Monitor cache performance
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/web-search/cache/stats"

# Check service status
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/web-search/status"
```

### Cache Management
```bash
# Clear search cache (if needed)
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/web-search/cache"
```

## FAQ

### Q: How much does web search cost?
A: Costs depend on your Brave Search API plan. The free tier includes limited searches per month. Caching helps reduce API calls and costs.

### Q: Can I disable web search for specific users?
A: Web search is controlled globally through configuration. Individual users cannot disable it, but administrators can remove the API key to disable it system-wide.

### Q: How often should I clear the cache?
A: Cache automatically expires based on TTL. Manual clearing is typically only needed for troubleshooting or when updating content quality requirements.

### Q: What happens if the web search API is down?
A: Lessons will continue to generate using RAG-only content. The system gracefully degrades when web search is unavailable.

### Q: Can I use a different search API?
A: Currently only Brave Search API is supported. Future versions may include additional search providers.

## Support and Resources

### Documentation
- [Web Search Integration Guide](WEB_SEARCH_INTEGRATION.md) - Comprehensive integration details
- [API Documentation](API.md) - Technical API reference
- [User Guide](USER_GUIDE.md) - Teacher-facing documentation

### External Resources
- [Brave Search API Documentation](https://brave.com/search/api/documentation/)
- [Brave Search API Dashboard](https://brave.com/search/api/)
- [Educational Content Guidelines](https://www.ed.gov/)

### Troubleshooting Support
1. Check application logs for detailed error messages
2. Review configuration validation output
3. Test API connectivity using curl commands
4. Contact support with configuration details and error logs

---

**Last Updated**: November 2025
**Version**: 1.0
**Compatible with**: PocketMusec v0.3.0+

For the most current information and updates, please refer to the main [Web Search Integration Documentation](WEB_SEARCH_INTEGRATION.md).