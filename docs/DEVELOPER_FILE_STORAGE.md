# Developer Guide: File Storage System

This guide provides detailed information for developers working with the PocketMusec File Storage System, including how to extend it, integration patterns, testing guidelines, and performance considerations.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Extending the File Storage System](#extending-the-file-storage-system)
4. [Integration Patterns](#integration-patterns)
5. [Testing Guidelines](#testing-guidelines)
6. [Performance Considerations](#performance-considerations)
7. [Best Practices](#best-practices)
8. [Troubleshooting for Developers](#troubleshooting-for-developers)

## Architecture Overview

The file storage system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              Frontend                   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   React UI  │  │ File Storage    │   │
│  │ Components  │  │     Hook        │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              API Layer                   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ FastAPI     │  │ File Storage    │   │
│  │   Routes    │  │   Endpoints     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Business Layer                │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ File Storage│  │   File          │   │
│  │   Manager    │  │ Repository      │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Data Layer                    │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  Database   │  │   File System   │   │
│  │  (SQLite)   │  │   Storage       │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Each layer has distinct responsibilities
2. **Dependency Injection**: Components are loosely coupled through injection
3. **Configuration-Driven**: Behavior controlled through configuration
4. **Error Resilience**: Graceful handling of failures with proper logging
5. **Security First**: All operations validated and authorized

## Core Components

### Backend Components

#### FileStorageManager (`backend/utils/file_storage.py`)

The `FileStorageManager` handles all physical file operations:

```python
class FileStorageManager:
    """Manages permanent file storage with organization and deduplication"""
    
    def __init__(self, storage_root: Optional[str] = None):
        """Initialize with configurable storage root"""
        
    def save_file_permanently(self, temp_file_path: str, original_filename: str) -> Tuple[str, str]:
        """Save file with UUID naming and date organization"""
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash for duplicate detection"""
        
    def is_allowed_extension(self, filename: str) -> bool:
        """Validate file extension against allowlist"""
        
    def is_valid_file_size(self, file_path: str) -> bool:
        """Check file size against configured limits"""
```

#### FileRepository (`backend/repositories/file_repository.py`)

The `FileRepository` manages database operations for file metadata:

```python
class FileRepository:
    """Repository for managing uploaded file records in the database"""
    
    def create_file_record(self, ...) -> str:
        """Create new file record with metadata"""
        
    def get_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Find duplicates by hash"""
        
    def update_ingestion_status(self, record_id: str, status: str, ...) -> bool:
        """Track processing status"""
        
    def list_files_by_status(self, status: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
        """List files with filtering and pagination"""
```

#### API Routes (`backend/api/routes/ingestion.py`)

FastAPI routes provide REST API endpoints:

```python
@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload and process document with permanent storage"""
    
@router.get("/files")
async def list_files(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List files with filtering and pagination"""
    
@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download file by ID"""
```

### Frontend Components

#### File Storage Types (`frontend/src/types/fileStorage.ts`)

TypeScript interfaces define the data structures:

```typescript
export interface FileMetadata {
  id: string;
  file_id: string;
  original_filename: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  ingestion_status: 'uploaded' | 'processing' | 'completed' | 'error';
  // ... other fields
}

export interface FileStorageResponse {
  success: boolean;
  file?: FileMetadata;
  files?: FileMetadata[];
  pagination?: PaginationInfo;
  error?: string;
}
```

#### useFileStorage Hook (`frontend/src/hooks/useFileStorage.ts`)

React hook provides state management and operations:

```typescript
export function useFileStorage(options: UseFileStorageOptions = {}): UseFileStorageReturn {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const loadFiles = useCallback(async (status?: string, page: number = 0) => {
    // Load files with filtering and pagination
  }, []);
  
  const downloadFile = useCallback(async (fileId: string, filename: string) => {
    // Handle file download
  }, []);
  
  // Return state and actions
}
```

#### IngestionService (`frontend/src/services/ingestionService.ts`)

Service handles API communication:

```typescript
class IngestionService {
  async ingestDocument(request: IngestionRequest): Promise<IngestionResponse> {
    // Upload and process document
  }
  
  async getUploadedFiles(status?: string, limit: number, offset: number): Promise<FileStorageResponse> {
    // List files from API
  }
  
  async downloadFile(fileId: string): Promise<Blob> {
    // Download file as blob
  }
}
```

## Extending the File Storage System

### Adding New File Types

To add support for new file types:

1. **Update Configuration** (`.env` or `backend/config.py`):

```python
# In config.py
@dataclass
class FileStorageConfig:
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ext.strip() for ext in os.getenv("ALLOWED_EXTENSIONS", 
            ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif,.svg,.mp3,.wav").split(",")
    ])
```

2. **Add MIME Type Detection** (if needed):

```python
# In FileStorageManager
def get_mime_type(self, filename: str) -> str:
    """Enhanced MIME type detection for new file types"""
    mime_type, _ = mimetypes.guess_type(filename)
    
    # Custom mappings for special types
    if filename.lower().endswith('.svg'):
        return 'image/svg+xml'
    elif filename.lower().endswith('.mp3'):
        return 'audio/mpeg'
    
    return mime_type or "application/octet-stream"
```

3. **Update Frontend Validation** (`frontend/src/constants/unified.ts`):

```typescript
export const FILE_STORAGE_CONSTANTS = {
  ALLOWED_EXTENSIONS: ['.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.svg'],
  SUPPORTED_MIME_TYPES: [
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/svg+xml'
  ],
};
```

### Implementing Custom Storage Providers

To support cloud storage (S3, Azure, etc.):

1. **Create Storage Provider Interface**:

```python
from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, local_path: str, remote_path: str) -> str:
        """Save file and return URL"""
        
    @abstractmethod
    async def get_file(self, remote_path: str) -> bytes:
        """Retrieve file content"""
        
    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file"""
        
    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists"""
```

2. **Implement S3 Provider**:

```python
class S3StorageProvider(StorageProvider):
    def __init__(self, bucket_name: str, aws_config: dict):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', **aws_config)
        
    async def save_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to S3"""
        self.s3_client.upload_file(local_path, self.bucket_name, remote_path)
        return f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}"
        
    # ... implement other methods
```

3. **Update FileStorageManager**:

```python
class FileStorageManager:
    def __init__(self, storage_root: Optional[str] = None, storage_provider: Optional[StorageProvider] = None):
        self.storage_root = Path(storage_root or config.file_storage.storage_root)
        self.storage_provider = storage_provider
        
    async def save_file_permanently(self, temp_file_path: str, original_filename: str) -> Tuple[str, str]:
        # ... existing validation logic
        
        if self.storage_provider:
            # Use cloud storage
            remote_url = await self.storage_provider.save_file(temp_file_path, relative_path)
            return unique_filename, remote_url
        else:
            # Use local storage
            final_path = self.storage_root / relative_path
            shutil.copy2(temp_file_path, final_path)
            return unique_filename, str(relative_path)
```

### Adding Custom File Processing

To add custom processing for specific file types:

1. **Create Processor Interface**:

```python
class FileProcessor(ABC):
    @abstractmethod
    async def can_process(self, file_metadata: Dict[str, Any]) -> bool:
        """Check if processor can handle the file"""
        
    @abstractmethod
    async def process(self, file_metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Process file and return results"""
```

2. **Implement Audio Processor**:

```python
class AudioProcessor(FileProcessor):
    async def can_process(self, file_metadata: Dict[str, Any]) -> bool:
        return file_metadata['mime_type'].startswith('audio/')
        
    async def process(self, file_metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        # Extract audio metadata, generate waveform, etc.
        duration = await self.get_audio_duration(file_path)
        waveform = await self.generate_waveform(file_path)
        
        return {
            'duration_seconds': duration,
            'waveform_data': waveform,
            'sample_rate': 44100,
            'channels': 2
        }
```

3. **Register Processor**:

```python
# In ingestion.py route
file_processors = [
    DocumentProcessor(),
    ImageProcessor(),
    AudioProcessor(),
    # Add more processors
]

async def process_file(file_metadata: Dict[str, Any], file_path: str):
    for processor in file_processors:
        if await processor.can_process(file_metadata):
            results = await processor.process(file_metadata, file_path)
            file_metadata['processing_results'].update(results)
            break
```

## Integration Patterns

### Pattern 1: Direct File Upload

For components that need to upload files directly:

```typescript
// React component example
function FileUploadComponent() {
  const { uploadProgress, uploadFile } = useFileUpload();
  
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      const result = await uploadFile(file, {
        onProgress: (progress) => uploadProgress.set(progress),
        metadata: { category: 'standards' }
      });
      
      console.log('Upload successful:', result);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };
  
  return <input type="file" onChange={handleFileSelect} />;
}
```

### Pattern 2: Background Processing

For long-running processing tasks:

```python
# Backend example
async def ingest_document_with_background_processing(file: UploadFile, user: User):
    # Save file immediately
    file_id, relative_path = file_storage.save_file_permanently(temp_path, file.filename)
    
    # Create database record
    record_id = file_repository.create_file_record(
        # ... metadata
        ingestion_status='uploaded'
    )
    
    # Queue background processing
    await queue_background_processing(record_id, file_id, relative_path)
    
    return {
        'success': True,
        'file_id': record_id,
        'status': 'queued_for_processing'
    }

# Background worker
async def background_processing_worker(record_id: str):
    try:
        file_repository.update_ingestion_status(record_id, 'processing')
        
        # Perform processing
        results = await process_document(record_id)
        
        file_repository.update_ingestion_status(
            record_id, 
            'completed',
            metadata_update={'processing_results': results}
        )
    except Exception as e:
        file_repository.update_ingestion_status(
            record_id, 
            'error',
            error_message=str(e)
        )
```

### Pattern 3: Streaming Upload

For large files with progress tracking:

```typescript
// Frontend streaming upload
async function uploadWithStream(file: File, onProgress: (progress: number) => void) {
  const chunkSize = 1024 * 1024; // 1MB chunks
  const totalChunks = Math.ceil(file.size / chunkSize);
  
  let uploadedChunks = 0;
  const chunks = [];
  
  for (let start = 0; start < file.size; start += chunkSize) {
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    chunks.push(chunk);
  }
  
  for (const chunk of chunks) {
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_index', uploadedChunks.toString());
    formData.append('total_chunks', totalChunks.toString());
    formData.append('file_id', file.id);
    
    await fetch('/api/ingestion/upload-chunk', {
      method: 'POST',
      body: formData
    });
    
    uploadedChunks++;
    onProgress((uploadedChunks / totalChunks) * 100);
  }
  
  // Signal upload complete
  await fetch('/api/ingestion/complete-upload', {
    method: 'POST',
    body: JSON.stringify({ file_id: file.id })
  });
}
```

### Pattern 4: File Preview Generation

For generating preview thumbnails:

```python
# Backend preview generation
class PreviewGenerator:
    async def generate_preview(self, file_path: str, file_metadata: Dict[str, Any]) -> str:
        """Generate preview and return preview file path"""
        
        if file_metadata['mime_type'].startswith('image/'):
            return await self.generate_image_preview(file_path)
        elif file_metadata['mime_type'] == 'application/pdf':
            return await self.generate_pdf_preview(file_path)
        elif file_metadata['mime_type'].startswith('audio/'):
            return await self.generate_audio_waveform(file_path)
        
        return None
    
    async def generate_pdf_preview(self, pdf_path: str) -> str:
        """Generate first page preview of PDF"""
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        page = doc[0]  # First page
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        
        preview_path = pdf_path.replace('.pdf', '_preview.png')
        pix.save(preview_path)
        
        doc.close()
        return preview_path
```

## Testing Guidelines

### Unit Testing

#### Backend Tests

```python
# tests/test_file_storage.py
import pytest
from unittest.mock import Mock, patch
from backend.utils.file_storage import FileStorageManager
from backend.repositories.file_repository import FileRepository

class TestFileStorageManager:
    @pytest.fixture
    def storage_manager(self, tmp_path):
        return FileStorageManager(storage_root=str(tmp_path))
    
    def test_save_file_permanently(self, storage_manager, tmp_path):
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Save file
        file_id, relative_path = storage_manager.save_file_permanently(
            str(test_file), "test.txt"
        )
        
        # Verify file was saved
        assert file_id is not None
        assert relative_path is not None
        assert storage_manager.file_exists(relative_path)
    
    def test_duplicate_detection(self, storage_manager):
        # Calculate hash for same content
        hash1 = storage_manager.calculate_file_hash("file1.txt")
        hash2 = storage_manager.calculate_file_hash("file2.txt")
        
        # Hashes should match for identical content
        assert hash1 == hash2
    
    def test_file_validation(self, storage_manager):
        # Test allowed extension
        assert storage_manager.is_allowed_extension("document.pdf")
        
        # Test disallowed extension
        assert not storage_manager.is_allowed_extension("script.exe")
```

#### Frontend Tests

```typescript
// frontend/src/hooks/__tests__/useFileStorage.test.ts
import { renderHook, act } from '@testing-library/react';
import { useFileStorage } from '../useFileStorage';
import { ingestionService } from '../../services/ingestionService';

// Mock the service
jest.mock('../../services/ingestionService');
const mockedIngestionService = ingestionService as jest.Mocked<typeof ingestionService>;

describe('useFileStorage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should load files on mount', async () => {
    const mockFiles = [
      { id: '1', original_filename: 'test.pdf', ingestion_status: 'completed' }
    ];

    mockedIngestionService.getUploadedFiles.mockResolvedValue({
      success: true,
      files: mockFiles
    });

    const { result } = renderHook(() => useFileStorage());

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.files).toEqual(mockFiles);
    expect(result.current.loading).toBe(false);
  });

  it('should handle download errors', async () => {
    mockedIngestionService.downloadFile.mockRejectedValue(
      new Error('Download failed')
    );

    const { result } = renderHook(() => useFileStorage());

    await act(async () => {
      try {
        await result.current.downloadFile('file1', 'test.pdf');
      } catch (error) {
        // Error is expected
      }
    });

    expect(result.current.error).toBe('Download failed');
  });
});
```

### Integration Testing

```python
# tests/test_integration_file_upload.py
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_file_upload_workflow():
    # 1. Upload file
    with open("tests/fixtures/test_document.pdf", "rb") as f:
        response = client.post(
            "/api/ingestion/ingest",
            files={"file": ("test_document.pdf", f, "application/pdf")},
            headers={"Authorization": "Bearer test_token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    file_id = data["file_metadata"]["id"]
    
    # 2. Check file status
    response = client.get(
        f"/api/ingestion/files/{file_id}",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["file"]["ingestion_status"] in ["uploaded", "processing", "completed"]
    
    # 3. Download file
    response = client.get(
        f"/api/ingestion/files/{file_id}/download",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    
    # 4. Delete file
    response = client.delete(
        f"/api/ingestion/files/{file_id}?delete_physical=true",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
```

### End-to-End Testing

```typescript
// tests/e2e/file-storage.e2e.test.ts
import { test, expect } from '@playwright/test';

test.describe('File Storage E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to file management
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'test@example.com');
    await page.fill('[data-testid=password]', 'password123');
    await page.click('[data-testid=login-button]');
    await page.goto('/file-management');
  });

  test('should upload and manage files', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/test-document.pdf');
    
    // Wait for upload to complete
    await expect(page.locator('[data-testid=upload-success]')).toBeVisible();
    
    // Verify file appears in list
    await expect(page.locator('[data-testid=file-list]')).toContainText('test-document.pdf');
    
    // Download file
    await page.click('[data-testid=download-button]');
    
    // Verify download started
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toBe('test-document.pdf');
  });

  test('should validate file types and sizes', async ({ page }) => {
    // Try uploading invalid file type
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/invalid-file.exe');
    
    // Should show error message
    await expect(page.locator('[data-testid=validation-error]')).toBeVisible();
    await expect(page.locator('[data-testid=validation-error]')).toContainText(
      'File type not supported'
    );
  });
});
```

## Performance Considerations

### File Storage Optimization

1. **Concurrent Uploads**:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedFileStorageManager(FileStorageManager):
    def __init__(self, *args, max_workers: int = 4, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def save_multiple_files(self, files: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Save multiple files concurrently"""
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(
                self.executor, 
                self.save_file_permanently, 
                temp_path, 
                filename
            )
            for temp_path, filename in files
        ]
        
        return await asyncio.gather(*tasks)
```

2. **Streaming for Large Files**:

```python
import aiofiles

async def stream_file_upload(file_path: str, chunk_size: int = 1024 * 1024):
    """Stream file upload in chunks"""
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk
```

3. **Caching Strategy**:

```python
from functools import lru_cache
import hashlib

class CachedFileRepository(FileRepository):
    @lru_cache(maxsize=128)
    def get_file_by_hash_cached(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Cached version of duplicate check"""
        return self.get_file_by_hash(file_hash)
    
    def clear_cache(self):
        """Clear the cache when files are added/removed"""
        self.get_file_by_hash_cached.cache_clear()
```

### Database Optimization

1. **Batch Operations**:

```python
def create_multiple_file_records(self, file_data_list: List[Dict[str, Any]]) -> List[str]:
    """Create multiple records in a single transaction"""
    record_ids = []
    
    with self.db_manager.get_connection() as conn:
        for file_data in file_data_list:
            record_id = str(uuid.uuid4())
            record_ids.append(record_id)
            
            conn.execute("""
                INSERT INTO uploaded_files (
                    id, file_id, original_filename, relative_path, 
                    file_hash, file_size, mime_type, user_id, 
                    metadata, ingestion_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                file_data['file_id'],
                file_data['original_filename'],
                file_data['relative_path'],
                file_data['file_hash'],
                file_data['file_size'],
                file_data['mime_type'],
                file_data.get('user_id'),
                json.dumps(file_data.get('metadata')),
                'uploaded',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
    
    return record_ids
```

2. **Query Optimization**:

```python
def get_files_with_filters(
    self, 
    filters: Dict[str, Any], 
    pagination: Dict[str, int]
) -> List[Dict[str, Any]]:
    """Optimized query with multiple filters"""
    
    query = "SELECT * FROM uploaded_files WHERE 1=1"
    params = []
    
    # Add filters dynamically
    if filters.get('status'):
        query += " AND ingestion_status = ?"
        params.append(filters['status'])
    
    if filters.get('user_id'):
        query += " AND user_id = ?"
        params.append(filters['user_id'])
    
    if filters.get('mime_type'):
        query += " AND mime_type = ?"
        params.append(filters['mime_type'])
    
    # Add pagination
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([pagination['limit'], pagination['offset']])
    
    with self.db_manager.get_connection() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
```

### Frontend Performance

1. **Virtual Scrolling**:

```typescript
// Large file list with virtual scrolling
import { FixedSizeList as List } from 'react-window';

interface VirtualizedFileListProps {
  files: FileMetadata[];
  onFileSelect: (file: FileMetadata) => void;
}

function VirtualizedFileList({ files, onFileSelect }: VirtualizedFileListProps) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style} onClick={() => onFileSelect(files[index])}>
      <FileListItem file={files[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={files.length}
      itemSize={60}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

2. **Lazy Loading**:

```typescript
// Intersection Observer for lazy loading
function useInfiniteScroll(loadMore: () => void, hasMore: boolean) {
  const loader = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore) {
          loadMore();
        }
      },
      { threshold: 1.0 }
    );
    
    if (loader.current) {
      observer.observe(loader.current);
    }
    
    return () => {
      if (loader.current) {
        observer.unobserve(loader.current);
      }
    };
  }, [loadMore, hasMore]);
  
  return loader;
}
```

## Best Practices

### Security Best Practices

1. **Always Validate Files**:

```python
def validate_file_security(self, file_path: str, filename: str) -> bool:
    """Comprehensive file security validation"""
    
    # Check file extension
    if not self.is_allowed_extension(filename):
        return False
    
    # Check file size
    if not self.is_valid_file_size(file_path):
        return False
    
    # Check magic bytes (file signature)
    if not self.validate_file_signature(file_path):
        return False
    
    # Scan for malware (if configured)
    if config.security.malware_scanning_enabled:
        if not self.scan_for_malware(file_path):
            return False
    
    return True
```

2. **Secure File Paths**:

```python
def get_secure_file_path(self, relative_path: str) -> Path:
    """Ensure file path is secure and within storage root"""
    
    # Normalize path
    normalized_path = Path(relative_path).resolve()
    
    # Ensure it stays within storage root
    try:
        full_path = self.storage_root / normalized_path
        full_path.resolve().relative_to(self.storage_root.resolve())
        return full_path
    except ValueError:
        # Path attempts to escape storage root
        raise SecurityError("Invalid file path")
```

### Error Handling Best Practices

1. **Structured Error Responses**:

```python
from enum import Enum

class FileStorageErrorType(Enum):
    VALIDATION_ERROR = "validation_error"
    STORAGE_ERROR = "storage_error"
    DATABASE_ERROR = "database_error"
    PERMISSION_ERROR = "permission_error"

class FileStorageError(Exception):
    def __init__(self, error_type: FileStorageErrorType, message: str, details: dict = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(message)
```

2. **Graceful Degradation**:

```typescript
 async function getFileListWithFallback(): Promise<FileMetadata[]> {
   try {
     // Try to get fresh data
     const response = await ingestionService.getUploadedFiles();
     return response.files || [];
   } catch (error) {
     console.warn('Failed to get fresh file list, using cache:', error);
     
     // Fallback to cached data if available
     try {
       const cachedData = localStorage.getItem('cachedFileList');
       return cachedData ? JSON.parse(cachedData) : [];
     } catch (cacheError) {
       console.error('Cache also failed:', cacheError);
       return [];
     }
   }
 }
```

### Code Organization Best Practices

1. **Dependency Injection**:

```python
# Use dependency injection for better testability
class FileUploadService:
    def __init__(
        self,
        storage_manager: FileStorageManager,
        repository: FileRepository,
        processor: FileProcessor
    ):
        self.storage_manager = storage_manager
        self.repository = repository
        self.processor = processor
    
    async def upload_file(self, file_data: FileData) -> FileMetadata:
        # Implementation using injected dependencies
        pass

# In tests, inject mock dependencies
test_service = FileUploadService(
    storage_manager=MockFileStorageManager(),
    repository=MockFileRepository(),
    processor=MockFileProcessor()
)
```

2. **Configuration-Driven Features**:

```python
# Use configuration for feature toggles
class FeatureFlagConfig:
    ENABLE_CLOUD_STORAGE: bool = False
    ENABLE_FILE_PREVIEW: bool = True
    ENABLE_VIRUS_SCANNING: bool = False
    MAX_CONCURRENT_UPLOADS: int = 3

# In code
if config.features.ENABLE_FILE_PREVIEW:
    preview = await generate_file_preview(file_path)
```

## Troubleshooting for Developers

### Common Development Issues

1. **File Permission Errors**:

```python
# Debug file permissions
import os

def debug_file_permissions(file_path: str):
    """Debug helper for file permission issues"""
    print(f"File path: {file_path}")
    print(f"Exists: {os.path.exists(file_path)}")
    print(f"Readable: {os.access(file_path, os.R_OK)}")
    print(f"Writable: {os.access(file_path, os.W_OK)}")
    print(f"Owner: {os.stat(file_path).st_uid}")
    print(f"Permissions: {oct(os.stat(file_path).st_mode)[-3:]}")
```

2. **Database Connection Issues**:

```python
# Debug database connections
def debug_database_connection(db_path: str):
    """Debug helper for database issues"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"SQLite version: {version}")
        
        # Check tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
```

3. **Memory Usage with Large Files**:

```python
import psutil
import tracemalloc

def debug_memory_usage():
    """Debug memory usage during file operations"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Trace memory allocations
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current: {current / 1024 / 1024:.2f} MB")
        print(f"Peak: {peak / 1024 / 1024:.2f} MB")
```

### Debug Mode Configuration

Enable comprehensive debug logging:

```python
# In config.py or .env
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# Enable specific debug modules
STORAGE_DEBUG=true
DATABASE_DEBUG=true
UPLOAD_DEBUG=true
```

### Test Data Management

Create test fixtures for consistent testing:

```python
# tests/fixtures/file_fixtures.py
import pytest
from pathlib import Path

@pytest.fixture
def test_pdf_file():
    """Create a test PDF file"""
    test_dir = Path("tests/fixtures")
    test_dir.mkdir(exist_ok=True)
    
    pdf_path = test_dir / "test_document.pdf"
    if not pdf_path.exists():
        # Create minimal PDF for testing
        create_minimal_pdf(pdf_path)
    
    return pdf_path

@pytest.fixture
def test_file_metadata():
    """Standard file metadata for testing"""
    return {
        "id": "test-file-id",
        "file_id": "test-uuid-filename",
        "original_filename": "test_document.pdf",
        "file_hash": "test-hash-value",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "ingestion_status": "uploaded"
    }
```

---

This guide provides comprehensive information for developers working with the PocketMusec File Storage System. For additional information, refer to the [File Storage System Documentation](FILE_STORAGE_SYSTEM.md) and the [API Documentation](API.md).