# File Storage Integration Guide

This guide explains how to integrate the new file storage system into your existing components.

## Overview

The file storage system provides:
- Permanent file storage with metadata tracking
- Duplicate file detection
- File download functionality
- Storage statistics and monitoring
- Error handling and validation

## Key Components

### 1. Types and Interfaces

Located in `src/types/fileStorage.ts`:
- `FileMetadata` - Complete file information including status and metadata
- `FileStorageResponse` - API response wrapper
- `FileStats` - Storage statistics
- `DuplicateFileWarning` - Duplicate file information

### 2. Service Layer

Updated `src/services/ingestionService.ts`:
- `getUploadedFiles()` - List uploaded files with filtering
- `getFileMetadata()` - Get detailed file information
- `downloadFile()` - Download original files
- `getFileStatistics()` - Get storage statistics

### 3. React Hooks

Located in `src/hooks/useFileStorage.ts`:
- `useFileStorage()` - Complete file storage management
- `useFileValidation()` - File validation utilities

### 4. UI Components

- `FileStoragePanel` - Compact panel for sidebar/right panel usage
- `FileManager` - Full-featured file management interface
- Updated `DocumentIngestion` - Enhanced with file storage features

## Integration Examples

### Basic Integration in RightPanel

```tsx
import FileStoragePanel from './FileStoragePanel';
import { useFileStorage } from '../../hooks/useFileStorage';

export default function RightPanel({ ...props }) {
  const { 
    recentlyUploaded, 
    fileStats, 
    downloadFile,
    loading,
    error 
  } = useFileStorage({ pageSize: 3 });

  // Add FileStoragePanel to your existing RightPanel JSX
  return (
    <aside>
      {/* Existing RightPanel content */}
      
      {/* Add file storage information */}
      <FileStoragePanel
        recentFiles={recentlyUploaded}
        fileStats={fileStats}
        onDownloadFile={downloadFile}
        onViewRecentFiles={() => {/* Navigate to file manager */}}
      />
    </aside>
  );
}
```

### Full File Manager Integration

```tsx
import FileManager from './FileManager';

export default function FilesPage() {
  const handleFileDownloaded = (fileId: string, filename: string) => {
    console.log(`File downloaded: ${filename}`);
    // Show success notification
  };

  const handleViewIngestion = () => {
    // Navigate to ingestion page
    window.location.href = '/ingestion';
  };

  return (
    <div className="container mx-auto p-6">
      <FileManager
        onViewIngestion={handleViewIngestion}
        onFileDownloaded={handleFileDownloaded}
      />
    </div>
  );
}
```

### Enhanced Document Ingestion

```tsx
import DocumentIngestion from '../DocumentIngestion';

export default function IngestionPage() {
  const handleIngestionComplete = (response: IngestionResponse) => {
    if (response.duplicate) {
      // Handle duplicate file
      console.log('Duplicate file detected:', response.existing_file);
    } else {
      // Handle successful ingestion
      console.log('File ingested successfully:', response.file_metadata);
    }
  };

  return (
    <DocumentIngestion
      onIngestionComplete={handleIngestionComplete}
    />
  );
}
```

## File Status Handling

The system tracks files through these statuses:

1. **uploaded** - File uploaded, waiting for processing
2. **processing** - File is being analyzed and ingested
3. **completed** - File successfully processed
4. **error** - Processing failed

```tsx
import { FILE_STATUS_LABELS, FILE_STATUS_COLORS } from '../../types/fileStorage';

function FileStatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${FILE_STATUS_COLORS[status]}`}>
      {FILE_STATUS_LABELS[status]}
    </span>
  );
}
```

## Error Handling

The system provides comprehensive error handling:

```tsx
import { FILE_STORAGE_MESSAGES } from '../../constants/unified';

function FileUploadError({ error }: { error: string }) {
  const getErrorMessage = (error: string) => {
    switch (error) {
      case 'File too large':
        return FILE_STORAGE_MESSAGES.FILE_TOO_LARGE;
      case 'Invalid file type':
        return FILE_STORAGE_MESSAGES.INVALID_FILE_TYPE;
      default:
        return error;
    }
  };

  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-4">
      <p className="text-red-800">{getErrorMessage(error)}</p>
    </div>
  );
}
```

## Storage Statistics

Display storage usage and statistics:

```tsx
import { useFileStorage } from '../../hooks/useFileStorage';
import { formatFileSize } from '../../types/fileStorage';

function StorageStats() {
  const { fileStats, loading } = useFileStorage();

  if (loading) return <div>Loading stats...</div>;
  if (!fileStats) return <div>No statistics available</div>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="text-center">
        <div className="text-2xl font-bold">{fileStats.total_files}</div>
        <div className="text-sm text-gray-600">Total Files</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold">{formatFileSize(fileStats.total_bytes)}</div>
        <div className="text-sm text-gray-600">Storage Used</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-green-700">{fileStats.completed_files}</div>
        <div className="text-sm text-gray-600">Completed</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-700">{fileStats.processing_files}</div>
        <div className="text-sm text-gray-600">Processing</div>
      </div>
    </div>
  );
}
```

## Duplicate File Detection

Handle duplicate files gracefully:

```tsx
import { DuplicateFileWarning } from '../../types/fileStorage';

function DuplicateWarning({ warning }: { warning: DuplicateFileWarning }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
      <h3 className="text-yellow-800 font-semibold mb-2">Duplicate File Detected</h3>
      <p className="text-yellow-700 mb-3">{warning.message}</p>
      <div className="text-sm text-yellow-600">
        <p>Existing file: {warning.existing_file.filename}</p>
        <p>Uploaded: {new Date(warning.existing_file.upload_date).toLocaleDateString()}</p>
        <p>Status: {warning.existing_file.status}</p>
      </div>
    </div>
  );
}
```

## Best Practices

1. **Always validate files** before upload using `useFileValidation()`
2. **Handle duplicate files** gracefully with informative user feedback
3. **Show file status** clearly in the UI with appropriate colors and labels
4. **Provide download links** for completed files
5. **Display storage statistics** to help users understand their usage
6. **Implement proper error handling** for all file operations
7. **Use the file storage hook** for consistent state management
8. **Display file metadata** including size, upload date, and processing status

## Migration from Old System

If migrating from the previous file handling system:

1. Replace direct file upload calls with `ingestionService.ingestDocument()`
2. Update UI to show new file metadata and status information
3. Add file download functionality
4. Implement duplicate file detection
5. Add storage statistics display
6. Update error handling to use new message constants

## Testing

Test the integration with:

1. **File upload validation** - Try uploading invalid file types and oversized files
2. **Duplicate detection** - Upload the same file twice
3. **Download functionality** - Verify completed files can be downloaded
4. **Status tracking** - Monitor files through processing states
5. **Error handling** - Test network failures and server errors
6. **Storage limits** - Verify file size and type restrictions