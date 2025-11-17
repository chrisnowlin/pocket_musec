# Presentation Management UI

This document describes the new UI interface for interacting with the backend presentation components.

## Overview

The presentation management system provides a comprehensive interface for:
- Creating presentations from lesson content
- Managing presentation generation jobs
- Viewing and exporting completed presentations
- Monitoring system health and performance

## Access

### Method 1: Direct URL
Navigate to `http://localhost:5173/presentations`

### Method 2: Through Settings
1. Go to the main application (`http://localhost:5173/`)
2. Click on "Settings" in the left sidebar
3. Look for the "Presentation System" card at the top
4. Click "Open Presentation Manager"

## Components

### 1. Presentation Creator (`/presentations/create`)
**Features:**
- Select lessons from your existing content
- Choose presentation styles (Default, Minimal, Corporate, Educational, Creative)
- Configure generation options:
  - AI polishing for enhanced content quality
  - Processing priority (Low, Normal, High, Urgent)
  - Generation timeout (15s to 2 minutes)
  - Maximum retry attempts
- Real-time progress tracking
- Error handling with recovery options

**Usage:**
1. Select a lesson from the dropdown
2. Choose your preferred style and options
3. Click "Generate Presentation"
4. Monitor progress in real-time
5. View the completed presentation

### 2. Presentation Management (`/presentations/manage`)
**Features:**
- View all presentation generation jobs
- Filter and sort jobs by status and priority
- Cancel running jobs
- Retry failed jobs
- Monitor job progress with visual indicators
- System health metrics dashboard

**Tabs:**
- **Generation Jobs**: List of all presentation generation jobs with status
- **Presentations**: View created presentations (placeholder for future enhancement)
- **System Health**: Performance metrics and statistics

### 3. Presentation Viewer (`/presentations/:presentationId`)
**Features:**
- Navigate through slides with previous/next controls
- View slide content including titles, key points, and teacher scripts
- Access presentation metadata (creation date, style, duration)
- Export presentations in multiple formats:
  - PowerPoint (PPTX)
  - PDF
  - JSON (raw data)
  - Markdown (text format)
- Download previously generated exports

## Workflow Example

### Creating a Presentation
1. **Access the Interface**: Go to Settings → Presentation System → Open Presentation Manager
2. **Create New**: Click "Create New Presentation" tab
3. **Select Content**: Choose a lesson from your existing lessons
4. **Customize**: Select style and generation options
5. **Generate**: Click "Generate Presentation" and wait for completion
6. **View**: Automatically redirected to view the completed presentation

### Managing Jobs
1. **View Jobs**: Go to "Manage Presentations" tab
2. **Monitor**: Watch job progress in real-time
3. **Control**: Cancel running jobs or retry failed ones
4. **Access**: Click the eye icon to view completed presentations

### Exporting Presentations
1. **Open Presentation**: Navigate to a specific presentation
2. **Switch to Export Tab**: Click "Export" in the top navigation
3. **Choose Format**: Select PPTX, PDF, JSON, or Markdown
4. **Download**: Click the export button to download the file

## Technical Features

### Real-time Updates
- Jobs are polled every 5 seconds for status updates
- Visual progress bars show generation progress
- Automatic refresh of job listings

### Error Handling
- Comprehensive error messages with recovery suggestions
- Automatic retry with fallback options (e.g., try without AI polishing)
- Graceful degradation for failed operations

### Performance Monitoring
- System health metrics dashboard
- Job success/failure rates
- Processing time statistics
- Queue health indicators

## Integration with Backend

The UI interfaces with the following backend endpoints:

### Generation
- `POST /api/presentations/generate` - Create presentation generation job
- `GET /api/presentations/jobs/{job_id}` - Get job status
- `GET /api/presentations/jobs` - List user jobs
- `DELETE /api/presentations/jobs/{job_id}` - Cancel job
- `POST /api/presentations/jobs/{job_id}/retry` - Retry failed job

### Viewing
- `GET /api/presentations/{presentation_id}` - Get presentation details
- `GET /api/presentations/{presentation_id}/export?format={format}` - Export presentation

### Monitoring
- `GET /api/presentations/jobs/health` - System health metrics
- `GET /api/presentations/jobs/statistics` - Detailed statistics

## File Structure

```
frontend/src/
├── components/presentation/
│   ├── PresentationManagement.tsx    # Main management interface
│   ├── PresentationCreator.tsx       # Presentation creation form
│   ├── PresentationViewer.tsx        # Slide viewer and export interface
│   └── PresentationNavigation.tsx    # Navigation card component
├── pages/
│   └── PresentationPage.tsx          # Page wrapper with tabs
└── App.tsx                          # Route definitions
```

## Future Enhancements

### Planned Features
- [ ] Presentation templates and custom themes
- [ ] Bulk presentation generation
- [ ] Presentation editing capabilities
- [ ] Advanced filtering and search
- [ ] Presentation sharing and collaboration
- [ ] Integration with external presentation tools
- [ ] Analytics dashboard for usage statistics

### UI Improvements
- [ ] Responsive design for mobile devices
- [ ] Dark mode support
- [ ] Keyboard shortcuts
- [ ] Drag-and-drop lesson selection
- [ ] Thumbnail previews of presentations

## Troubleshooting

### Common Issues

1. **Lesson Selection Empty**
   - Ensure you have created lessons in the main application
   - Check if lessons are marked as completed (not drafts)

2. **Generation Fails**
   - Try reducing timeout or priority settings
   - Check backend logs for detailed error messages
   - Retry with AI polishing disabled

3. **Export Downloads Don't Work**
   - Check browser download settings
   - Ensure the presentation generation completed successfully
   - Try a different export format

4. **Jobs Don't Update**
   - Refresh the page to reconnect
   - Check network connection
   - Verify backend is running on port 8000

### Support

For technical issues or questions:
1. Check the browser console for error messages
2. Review the backend logs (running on port 8000)
3. Ensure both frontend and backend services are running
4. Verify API endpoints are accessible