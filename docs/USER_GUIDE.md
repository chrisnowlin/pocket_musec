# PocketMusec User Guide - Web Interface

Complete guide to using PocketMusec's web interface for AI-powered music lesson planning.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Lesson Generation](#lesson-generation)
4. [Image Management](#image-management)
5. [Embeddings Management](#embeddings-management)
6. [Settings Configuration](#settings-configuration)
7. [Advanced Features](#advanced-features)
8. [Tips and Best Practices](#tips-and-best-practices)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing PocketMusec

1. Open your web browser
2. Navigate to `http://localhost:5173` (or your deployed URL)
3. The web interface will load with the main dashboard

### First-Time Setup

1. **Processing Mode Selection**: Choose between Cloud (fast) or Local (private) processing
2. **Model Download** (if using Local mode): Download the required AI model
3. **Storage Configuration**: Set your preferred storage quotas and locations

## Dashboard Overview

The main dashboard provides access to all PocketMusec features through an intuitive sidebar navigation:

### Sidebar Navigation

- **Home**: Main dashboard with quick actions and status overview
- **New Lesson**: Start creating a new lesson plan
- **Upload Images**: Manage and process sheet music and instructional images
- **Embeddings**: Advanced semantic search and embeddings management
- **Settings**: Configure processing modes, models, and preferences
- **Sessions**: View and manage previous lesson planning sessions

### Status Indicators

The dashboard displays real-time status information:
- **Processing Mode**: Current mode (Cloud/Local) and model status
- **Storage Usage**: Current usage and available space
- **Recent Activity**: Latest lessons, uploads, and searches

## Lesson Generation

### Creating a New Lesson

1. Click **"New Lesson"** in the sidebar
2. **Lesson Configuration**:
   - Enter lesson title and objectives
   - Select grade level and standards
   - Add context and requirements

3. **Add Context**:
   - Upload relevant images (sheet music, diagrams)
   - Add previous lesson references
   - Include specific topics or concepts

4. **Generate Lesson**:
   - Click **"Generate Lesson"** to start AI creation
   - Monitor progress with real-time status updates
   - Review generated content

5. **Refine and Export**:
   - Edit generated content as needed
   - Add citations and references
   - Export as Markdown or PDF

### Lesson Features

- **Standards Alignment**: Automatic alignment with National Core Arts Standards
- **Web-Enhanced Content**: Integration of current educational resources and research
- **Citation Tracking**: Automatic source tracking and IEEE formatting
- **Context Integration**: Seamless integration with uploaded images
- **Export Options**: Multiple formats for different use cases

### Web-Enhanced Lesson Planning

PocketMusec enhances lesson planning with real-time web search capabilities:

#### How Web Search Works

1. **Automatic Detection**: The system identifies when web search would benefit your lesson
2. **Educational Filtering**: Results are filtered for quality educational content
3. **Intelligent Integration**: Web content is seamlessly woven into lesson plans
4. **Source Quality**: Priority given to educational institutions (.edu, .org, .gov)

#### Benefits for Teachers

- **Current Research**: Access to latest music education methodologies and findings
- **Diverse Resources**: Multiple perspectives from educational institutions worldwide
- **Time Savings**: Curated educational content without manual searching
- **Professional Growth**: Stay current with pedagogical advances and trends
- **Student Engagement**: Fresh examples and activities from contemporary sources

#### Web Search Indicators

When web search enhances your lesson, you'll see:

```
🔍 Web-Enhanced Lesson
• 5 educational resources found
• Sources: .edu, .org institutions
• Relevance: 0.82 average score
```

#### Example: Web-Enhanced vs. Standard Lesson

**Standard Lesson:**
```
Topic: Rhythm for Grade 3
- Basic rhythm concepts
- Quarter and eighth notes
- Simple clapping exercises
```

**Web-Enhanced Lesson:**
```
Topic: Rhythm for Grade 3
- Basic rhythm concepts with modern methodologies
- Quarter and eighth notes using current research
- Cross-cultural rhythm activities (Berklee Music College)
- Interactive digital rhythm tools (Music Educators Association)
- Assessment strategies from recent educational studies
```

#### Managing Web Search Settings

1. **Navigate to Settings** in the sidebar
2. **Select Web Search Configuration**
3. **Configure Options:**
   - Enable/disable web search integration
   - Set educational content filtering preferences
   - Adjust relevance score thresholds
   - Configure cache settings for performance

For detailed web search configuration, see the [Web Search Configuration Guide](WEB_SEARCH_CONFIGURATION.md).

## Image Management

### Uploading Images

1. Navigate to **"Upload Images"** in the sidebar
2. **Drag and Drop**: Simply drag image files onto the upload area
3. **Batch Upload**: Select multiple files for simultaneous upload
4. **Processing Options**:
   - Choose processing mode (Cloud/Local)
   - Add custom vision prompts
   - Set metadata and tags

### Image Processing

Each uploaded image undergoes:
- **OCR Text Extraction**: Text recognition using Tesseract
- **Vision AI Analysis**: Semantic understanding of content
- **Metadata Extraction**: Automatic tagging and categorization
- **Storage Optimization**: Efficient compression and organization

### Image Gallery

- **Search and Filter**: Find images by content, tags, or date
- **Preview**: Quick preview of images and extracted text
- **Edit**: Modify metadata and analysis results
- **Delete**: Remove unused images to free storage space

### Supported Formats

- **Images**: PNG, JPEG, GIF, WebP (max 10MB per file)
- **Content**: Sheet music, diagrams, instructional materials
- **Quality**: High-resolution recommended for best OCR results

## Embeddings Management

The embeddings system provides powerful semantic search capabilities for music education standards and objectives.

### Statistics Dashboard

Access the **Statistics** tab to view:
- **Embedding Counts**: Number of standards and objectives embedded
- **Storage Usage**: Database size and efficiency metrics
- **Generation History**: Track embedding generation over time
- **Export Options**: Download statistics in CSV or JSON format

### Generating Embeddings

1. Navigate to **"Generate"** tab
2. **Generation Options**:
   - Force regeneration of existing embeddings
   - Batch size configuration
   - Progress tracking

3. **Monitor Progress**:
   - Real-time progress bar
   - Success/failure/skipped counts
   - Error details and retry options

### Semantic Search

1. Navigate to **"Search"** tab
2. **Search Configuration**:
   - Natural language query (e.g., "musical scales for beginners")
   - Grade level filtering
   - Strand selection (Creating, Performing, Responding, Connecting)
   - Similarity threshold adjustment

3. **Search Results**:
   - Similarity scores for each result
   - Pagination for large result sets
   - Virtual scrolling for smooth navigation
   - Export search results

### Advanced Search Features

- **Pagination**: Navigate through large result sets efficiently
- **Virtual Scrolling**: Enable for smooth performance with >20 results
- **Filtering**: Refine results by grade, strand, or similarity
- **Export**: Download search results in various formats

### Usage Analytics

Track your embeddings usage in the **"Usage"** tab:
- **Search Statistics**: Total searches, weekly activity
- **Generation Metrics**: Embedding generation history
- **Activity Trends**: Visual representation of usage patterns
- **Export Data**: Download usage analytics

### Batch Operations

Perform bulk operations in the **"Batch"** tab:
- **Regenerate All**: Update all embeddings with latest models
- **Clear All**: Remove all embeddings (with confirmation)
- **Refresh Cache**: Update cached statistics
- **Progress Tracking**: Monitor long-running operations

## Settings Configuration

### Processing Modes

#### Cloud Mode
- **Speed**: Fastest processing with latest AI models
- **Requirements**: Active internet connection and API key
- **Privacy**: Data processed on external servers
- **Cost**: May incur API usage charges

#### Local Mode
- **Privacy**: All processing on your machine
- **Offline**: Works without internet connection
- **Setup**: Requires model download and sufficient RAM
- **Cost**: No ongoing API charges

### Model Management

- **Model Status**: Check if local model is installed and running
- **Download Models**: Get required models for local processing
- **Version Updates**: Keep models up to date
- **Resource Usage**: Monitor memory and CPU usage

### Storage Configuration

- **Image Storage**: Set quotas and locations for image files
- **Database Management**: Configure database location and backups
- **Cleanup Options**: Automatic cleanup of old files
- **Usage Monitoring**: Track storage utilization

### API Configuration

- **API Keys**: Configure Chutes API key for cloud mode
- **Endpoints**: Set custom API endpoints if needed
- **Rate Limits**: Configure request limits and timeouts
- **Authentication**: Manage API authentication settings

## Advanced Features

### Virtual Scrolling

For large result sets, enable virtual scrolling:
- **Performance**: Renders only visible items
- **Memory Efficiency**: Reduces memory usage
- **Smooth Scrolling**: Maintains 60fps performance
- **Accessibility**: Full keyboard navigation support

### Export Functionality

Export various data types:
- **Statistics**: Embedding counts and metrics
- **Usage Data**: Search and generation analytics
- **Search Results**: Semantic search results with metadata
- **Formats**: CSV, JSON, and downloadable files

### Accessibility Features

PocketMusec is WCAG 2.1 AA compliant:
- **Keyboard Navigation**: Full keyboard access to all features
- **Screen Reader Support**: ARIA labels and semantic HTML
- **High Contrast**: Clear visual indicators and text
- **Focus Management**: Logical tab order and focus indicators

### Error Recovery

- **Automatic Retry**: Failed requests are retried with exponential backoff
- **Error Messages**: Clear, actionable error descriptions
- **Graceful Degradation**: Features work even with partial failures
- **Progress Preservation**: Work is saved during interruptions

## Tips and Best Practices

### Lesson Generation

- **Specific Prompts**: Provide detailed, specific objectives
- **Context Richness**: Include relevant images and examples
- **Standards Alignment**: Review generated content against standards
- **Web Search Optimization**: Use clear, educational terms for better web results
- **Iterative Refinement**: Generate multiple versions and combine best elements

### Web-Enhanced Planning

- **Educational Keywords**: Include "teaching", "curriculum", "lesson plan" in prompts
- **Grade Context**: Specify grade level for age-appropriate web content
- **Subject Focus**: Use music-specific terminology for targeted results
- **Quality Review**: Evaluate web sources for educational appropriateness
- **Source Verification**: Check credibility of external educational resources

### Image Management

- **High Quality**: Use high-resolution images for best OCR results
- **Descriptive Names**: Use descriptive filenames for easier searching
- **Regular Cleanup**: Remove unused images to maintain performance
- **Batch Processing**: Upload multiple related images together

### Embeddings Usage

- **Natural Language**: Use conversational queries for semantic search
- **Filtering**: Apply filters to narrow down results
- **Export Results**: Save useful searches for future reference
- **Regular Updates**: Regenerate embeddings when standards change

### Performance Optimization

- **Virtual Scrolling**: Enable for large result sets
- **Local Mode**: Use for privacy-sensitive content
- **Storage Management**: Monitor and clean up regularly
- **Browser Updates**: Keep browser updated for best performance

## Troubleshooting

### Common Issues

#### Lesson Generation Fails
- **Check Processing Mode**: Ensure selected mode is properly configured
- **Verify API Key**: For cloud mode, check API key is valid
- **Model Status**: For local mode, ensure model is downloaded and running
- **Internet Connection**: Check connectivity for cloud mode

#### Image Upload Errors
- **File Format**: Ensure image is in supported format (PNG, JPEG, GIF, WebP)
- **File Size**: Check file is under 10MB limit
- **Storage Space**: Verify sufficient storage quota is available
- **OCR Service**: Ensure Tesseract is properly configured

#### Web Search Issues
- **API Key**: Verify Brave Search API key is configured by administrator
- **Network Connection**: Check internet connectivity for web search functionality
- **Content Quality**: Adjust relevance threshold if results seem irrelevant
- **Search Timeouts**: Increase timeout settings for slow network connections

#### Search Performance Issues
- **Enable Virtual Scrolling**: For large result sets
- **Reduce Batch Size**: For generation operations
- **Check Filters**: Ensure search filters are appropriate
- **Clear Cache**: Refresh embeddings cache if needed

#### Model Download Problems
- **Internet Connection**: Ensure stable connection for downloads
- **Disk Space**: Verify sufficient space for model files (~5GB)
- **Permissions**: Check write permissions for model directory
- **Antivirus**: Temporarily disable if blocking downloads

### Error Messages

#### "Processing Mode Unavailable"
- **Solution**: Switch to available mode or configure missing requirements

#### "Storage Quota Exceeded"
- **Solution**: Delete unused files or increase quota in settings

#### "Model Not Found"
- **Solution**: Download required model in settings

#### "Web Search Unavailable"
- **Solution**: Contact administrator to configure Brave Search API, lessons will continue with RAG-only content

#### "API Request Failed"
- **Solution**: Check API key, internet connection, or switch to local mode

### Getting Help

1. **Check Documentation**: Review relevant sections in this guide
2. **Error Logs**: Check browser console and server logs
3. **Community Support**: Visit GitHub Discussions
4. **Report Issues**: File detailed bug reports on GitHub Issues

### Performance Tips

- **Browser Choice**: Use modern browsers (Chrome, Firefox, Safari, Edge)
- **Memory Management**: Close unused browser tabs
- **Regular Updates**: Keep application and models updated
- **Network Stability**: Use stable internet connection for cloud mode

---

This user guide covers all features of PocketMusec's web interface. For technical details and API documentation, see the [API Reference](API.md). For developer information, see the [Developer Setup Guide](DEVELOPER_SETUP.md).