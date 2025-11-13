# CLI to Web Migration Guide

## Overview

This guide helps users transition from PocketMusec CLI commands to the web interface. The web interface provides equivalent functionality with an enhanced user experience.

## Quick Reference

| CLI Command | Web Interface Path | Steps |
|-------------|-------------------|-------|
| `pocketmusec ingest standards file.pdf` | **Document Ingestion** | 1. Navigate to Ingestion → 2. Upload file → 3. Confirm → 4. Process |
| `pocketmusec ingest auto file.pdf` | **Document Ingestion** | Same as above (auto-classification is built-in) |
| `pocketmusec generate lesson` | **Chat Interface** | 1. Navigate to Workspace → 2. Start new conversation → 3. Chat with AI |
| `pocketmusec embeddings generate` | **Settings → Embeddings** | 1. Go to Settings → 2. Click "Generate Embeddings" → 3. Configure options |
| `pocketmusec embeddings stats` | **Settings → Embeddings** | 1. Go to Settings → 2. View statistics dashboard |
| `pocketmusec embeddings search "query"` | **Standards Browser** | 1. Go to Browse → 2. Use search bar → 3. Apply filters |

## Detailed Migration Instructions

### 1. Document Ingestion

#### CLI Command:
```bash
pocketmusec ingest standards "NC Music Standards.pdf" --force --use-vision
```

#### Web Interface Equivalent:

1. **Navigate to Document Ingestion**
   - Click "Ingestion" in the sidebar
   - Or go directly to `/ingestion` in your browser

2. **Upload Your Document**
   - Drag and drop the PDF file onto the upload area
   - Or click "Select PDF File" to browse

3. **Review Classification Results**
   - The system automatically classifies your document
   - Review the document type and confidence level
   - View the description to confirm it's correct

4. **Configure Advanced Options (Optional)**
   - Click "Advanced Options" if needed
   - Select processing preferences:
     - Vision AI processing (more accurate, slower)
     - Fast table-based processing
     - Force re-ingestion
     - Preview results

5. **Process the Document**
   - Click "Proceed with Ingestion"
   - Monitor progress in real-time
   - View detailed results when complete

6. **Review Results**
   - See counts of processed items
   - View statistics and metrics
   - Option to ingest another document

#### Benefits of Web Interface:
- **Visual Progress**: Real-time progress indicators
- **Error Handling**: Clear error messages and recovery options
- **Batch Processing**: Easy to process multiple documents
- **Results Dashboard**: Comprehensive results visualization

### 2. Lesson Generation

#### CLI Command:
```bash
pocketmusec generate lesson --interactive
```

#### Web Interface Equivalent:

1. **Start a New Session**
   - Navigate to the main workspace
   - Click "New Conversation" in the sidebar
   - Or refresh to start fresh

2. **Set Your Context**
   - Use the right panel to configure:
     - Grade level
     - Strand
     - Standard (optional)
     - Lesson duration
     - Class size
     - Additional context

3. **Natural Conversation**
   - Type your lesson planning needs naturally
   - Example: "I need a 3rd grade rhythm lesson for a 30-minute class with recorders"
   - The AI will understand and suggest relevant standards

4. **Interactive Planning**
   - AI suggests relevant standards automatically
   - Provides activity ideas and teaching strategies
   - Ask follow-up questions to refine the plan

5. **Generate Lesson**
   - When ready, say "generate lesson plan" or "create lesson"
   - AI generates a comprehensive lesson plan
   - Review and edit as needed

6. **Save and Export**
   - Lesson is automatically saved as a draft
   - Export to various formats
   - Continue editing in the built-in editor

#### Benefits of Web Interface:
- **Natural Language**: No rigid forms, just conversation
- **Real-time Suggestions**: AI provides immediate feedback
- **Visual Standards**: See standards in context
- **Draft Management**: Automatic saving and version control
- **Rich Editor**: Built-in lesson editing tools

### 3. Embeddings Management

#### CLI Commands:
```bash
# Generate embeddings
pocketmusec embeddings generate --force --batch-size 10

# View statistics
pocketmusec embeddings stats

# Search embeddings
pocketmusec embeddings search "rhythm activities" --grade "3rd Grade" --limit 5
```

#### Web Interface Equivalent:

1. **Access Embeddings Management**
   - Go to Settings in the sidebar
   - Click on "Embeddings Management"

2. **Generate Embeddings**
   - Click "Generate New Embeddings"
   - Configure options:
     - Force regeneration (checkbox)
     - Batch size (slider)
     - Processing mode selection
   - Click "Start Generation"
   - Monitor progress with visual indicators

3. **View Statistics**
   - Statistics dashboard shows:
     - Total standard embeddings
     - Total objective embeddings
     - Embedding dimension
     - Last updated timestamp
     - Processing status

4. **Search Embeddings**
   - Use the search bar at the top
   - Enter natural language queries
   - Apply filters:
     - Grade level dropdown
     - Strand dropdown
     - Similarity threshold slider
     - Result limit
   - View ranked results with similarity scores

5. **Manage Embeddings**
   - Clear all embeddings (with confirmation)
   - View prepared texts
   - Download embedding statistics
   - Schedule automatic regeneration

#### Benefits of Web Interface:
- **Visual Dashboard**: At-a-glance statistics
- **Interactive Search**: Real-time search results
- **Progress Tracking**: Visual generation progress
- **Easy Management**: One-click operations
- **Filtering**: Advanced search filters

## Advanced Features

### Session Management

#### CLI: Limited session handling
#### Web: Comprehensive session management
- View all previous conversations
- Resume interrupted sessions
- Export conversation history
- Delete unwanted sessions
- Organize by date or topic

### Draft Management

#### CLI: Basic file output
#### Web: Advanced draft system
- Automatic draft saving
- Version history tracking
- Built-in editor with syntax highlighting
- Export to multiple formats
- Collaboration features

### Real-time Updates

#### CLI: Static output
#### Web: Live updates
- Streaming responses
- Progress indicators
- Real-time status updates
- Interactive notifications
- Live collaboration

## Troubleshooting

### Common Issues and Solutions

#### Document Upload Fails
- **Check file format**: Only PDF files are supported
- **Check file size**: Large files may timeout
- **Check network**: Stable connection required
- **Solution**: Use smaller files or check connection

#### Lesson Generation Slow
- **Check processing mode**: Cloud vs Local processing
- **Check embeddings**: Ensure embeddings are generated
- **Solution**: Generate embeddings first, check settings

#### Search Results Poor
- **Check embeddings**: May need regeneration
- **Check query terms**: Try different keywords
- **Check filters**: Adjust grade/strand filters
- **Solution**: Regenerate embeddings with updated data

### Getting Help

#### Web Interface Help:
- **In-app guidance**: Tooltips and help text
- **Interactive tutorials**: Step-by-step walkthroughs
- **Contextual help**: Help buttons on each page
- **Status indicators**: Clear error messages

#### Additional Resources:
- **User Guide**: Comprehensive documentation
- **Video Tutorials**: Visual walkthroughs
- **Community Forum**: User discussions and tips
- **Support Chat**: Direct assistance

## Tips for Effective Migration

### 1. Start Simple
- Begin with basic document ingestion
- Try lesson generation with simple requests
- Gradually explore advanced features

### 2. Use Natural Language
- Instead of specific commands, describe what you want
- Example: "I need a kindergarten melody lesson" vs. selecting options
- The AI understands context and intent

### 3. Leverage the Interface
- Use drag-and-drop for file uploads
- Take advantage of real-time suggestions
- Explore the rich filtering and search options

### 4. Organize Your Work
- Use descriptive names for conversations
- Save important lessons as drafts
- Use the session history to track progress

### 5. Explore Features
- Try the advanced options in document ingestion
- Experiment with different search queries
- Use the built-in editor for lesson refinement

## Keyboard Shortcuts

### Navigation Shortcuts
- `Ctrl + /`: Show keyboard shortcuts
- `Ctrl + K`: Quick search
- `Ctrl + N`: New conversation
- `Ctrl + S`: Save current work

### Editing Shortcuts
- `Ctrl + B`: Bold text
- `Ctrl + I`: Italic text
- `Ctrl + Z`: Undo
- `Ctrl + Y`: Redo

### Interface Shortcuts
- `Esc`: Close modal/dialog
- `Enter`: Confirm action
- `Tab`: Navigate between fields
- `Space`: Toggle checkboxes

## Performance Tips

### Optimize Your Experience

1. **Browser Choice**: Use modern browsers (Chrome, Firefox, Safari, Edge)
2. **Network Connection**: Stable internet connection for best performance
3. **File Management**: Keep file sizes reasonable for uploads
4. **Session Management**: Close unused sessions to improve performance
5. **Regular Updates**: Keep your browser updated for best compatibility

### Recommended Settings

- **Processing Mode**: Cloud for reliability, Local for privacy
- **Auto-save**: Enable for draft protection
- **Notifications**: Enable for important updates
- **Theme**: Choose based on your preference (light/dark)

## Conclusion

The web interface provides all CLI functionality with significant enhancements:

- **Better User Experience**: Visual, interactive, and intuitive
- **More Features**: Advanced capabilities not possible in CLI
- **Easier Collaboration**: Share and work together
- **Better Accessibility**: Works on any device with a browser
- **Real-time Updates**: Live feedback and progress tracking

The migration is straightforward, and most users find the web interface more powerful and easier to use than the CLI commands.

## Need Help?

If you need assistance with the migration:
1. Check the in-app help system
2. Review the user documentation
3. Contact support through the help menu
4. Join the community forum for user tips

Welcome to the enhanced PocketMusec web experience!