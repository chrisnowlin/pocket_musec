# Citation System Implementation

## Overview

This document describes the complete citation system implementation for the frontend, which enhances the user experience by displaying source file information alongside citations and providing direct access to source documents.

## Features Implemented

### 1. Enhanced Citation Display
- **File Information Display**: Shows filename, file type, and file size alongside citations
- **Download Functionality**: Direct download links to source documents from citations
- **File Metadata Display**: Shows upload date and processing status in citation tooltips
- **Backward Compatibility**: Handles both new file_id-based and legacy source_document references

### 2. TypeScript Types and Interfaces
- **Citation**: Core citation structure with file_id support
- **FileCitation**: Citation combined with file metadata
- **EnhancedCitation**: Complete citation information with file details and availability
- **CitationServiceResponse**: API response structure for citation operations

### 3. React Components
- **CitationCard**: Individual citation display with file information, download, and expandable details
- **CitationList**: Container for multiple citations with bulk actions and availability summary
- **CitationTooltip**: Inline citation display with hover information
- **CitationErrorBoundary**: Error handling component for graceful failure recovery

### 4. React Hooks
- **useCitations**: Main hook for fetching and managing enhanced citations
- **useCitation**: Hook for individual citation operations
- **useLegacyCitations**: Hook for handling legacy string-based citations

### 5. Services
- **citationService**: Service for fetching citations, file metadata, and handling downloads
- **FileStorageService**: Integration with existing file storage system
- **Caching**: Built-in caching for performance optimization

### 6. Error Handling
- **Graceful Degradation**: Fallbacks for missing or unavailable file information
- **Error Boundaries**: Component-level error handling
- **Mixed Format Support**: Handles both old and new citation formats seamlessly

## File Structure

```
frontend/src/
├── types/
│   └── fileStorage.ts                    # Enhanced citation types
├── components/unified/
│   ├── CitationCard.tsx                  # Individual citation component
│   ├── CitationList.tsx                  # Citation list component
│   ├── CitationTooltip.tsx               # Tooltip component
│   ├── CitationErrorBoundary.tsx         # Error boundary
│   └── ChatMessage.tsx                   # Updated with citation display
├── services/
│   └── citationService.ts                # Citation service implementation
├── hooks/
│   └── useCitations.ts                   # Citation hooks
├── utils/
│   ├── citationUtils.ts                  # Citation utilities
│   └── citationTestUtils.ts              # Test utilities
└── docs/
    └── CITATION_IMPLEMENTATION.md        # This documentation
```

## Usage Examples

### Basic Citation Display

```tsx
import { useCitations } from '../hooks/useCitations';
import { CitationList } from '../components/unified/CitationList';

function LessonCitations({ lessonId }: { lessonId: string }) {
  const { citations, isLoading, error } = useCitations(lessonId);
  
  if (isLoading) return <div>Loading citations...</div>;
  if (error) return <div>Error loading citations</div>;
  
  return (
    <CitationList
      citations={citations}
      lessonId={lessonId}
      onViewInContext={(citation) => {
        // Handle citation context view
      }}
    />
  );
}
```

### Individual Citation with File Information

```tsx
import { CitationCard } from '../components/unified/CitationCard';

function CitationExample({ citation }: { citation: string }) {
  const { enhancedCitation } = useCitation(citation, 'lesson-123');
  
  return (
    <CitationCard
      citation={citation}
      enhancedCitation={enhancedCitation}
      isExpanded={false}
      onToggle={() => {}}
      onViewInContext={() => {}}
      onDownload={(fileCitation) => {
        // Handle file download
      }}
    />
  );
}
```

### Service Usage

```tsx
import { citationService } from '../services/citationService';

// Fetch enhanced citations
const citations = await citationService.getLessonCitations('lesson-123');

// Download file from citation
await citationService.downloadCitationFile(fileId);

// Get file metadata
const metadata = await citationService.getCitationFileMetadata(fileId);
```

## Error Handling

The implementation includes comprehensive error handling:

1. **Missing File Information**: When file metadata is unavailable, citations display with fallback information
2. **Deleted Files**: Handles cases where source files have been deleted
3. **Network Errors**: Graceful handling of API failures with retry logic
4. **Mixed Formats**: Supports both legacy string citations and new enhanced citations

## Browser Compatibility

The citation system is compatible with modern browsers that support:
- ES6+ (Object spread, async/await)
- React 18+ (Hooks, Suspense)
- TypeScript 4.5+
- Fetch API

## Testing

### Integration Testing

Run the integration test to verify the implementation:

```javascript
// In browser console
import('./test-citation-integration').then(m => m.runCitationIntegrationTest())
// or
window.runCitationIntegrationTest()
```

### Test Coverage

The implementation includes tests for:
- Citation normalization and validation
- File metadata formatting
- Error handling scenarios
- Component integration
- Service functionality

## Performance Considerations

1. **Caching**: Citation data and file metadata are cached to reduce API calls
2. **Lazy Loading**: Citations are loaded on-demand with debouncing
3. **Memoization**: Components use React.memo to prevent unnecessary re-renders
4. **Virtualization**: Large citation lists can be virtualized (implementation ready)

## Accessibility

The citation components include:
- Proper ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

## Future Enhancements

Potential future improvements:
1. **Citation Analytics**: Track citation usage and downloads
2. **Advanced Search**: Search within citation content
3. **Export Options**: Export citations with file references
4. **Collaboration Features**: Share and annotate citations
5. **Offline Support**: Cache citations for offline viewing

## Migration Guide

### From Legacy Citations

1. Replace string citation references with Citation objects
2. Update citation display components to use new CitationCard/CitationList
3. Implement file download handling
4. Add error boundaries for graceful degradation

### API Integration

Ensure the backend supports:
- Citation endpoints with file_id references
- File metadata endpoints
- Download endpoints for source files
- Error responses for missing files

## Support

For questions or issues with the citation implementation:
1. Check the browser console for error messages
2. Run the integration test to verify functionality
3. Review the error handling documentation
4. Check network requests in browser dev tools

---

**Implementation Status**: ✅ Complete

This citation system provides a robust, user-friendly way to display and interact with source file information in citations, enhancing the overall user experience and making citations more actionable and informative.