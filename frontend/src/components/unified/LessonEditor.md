# LessonEditor Component

A comprehensive markdown editor component built for the PocketMusec application, providing live preview, auto-save functionality, and recovery capabilities for lesson content editing.

## Features

### Core Functionality
- **Markdown Editing**: Full-featured textarea with monospace font for code-like editing experience
- **Live Preview**: Split-screen preview mode using the existing MarkdownRenderer component
- **Three View Modes**: Edit, Preview, and Split-screen layouts
- **Auto-save**: Debounced saving with configurable timing (2s after typing + every 30s)
- **Browser Recovery**: IndexedDB-based storage for crash recovery and session restoration
- **Keyboard Shortcuts**: Ctrl+S for save, Esc for cancel/exit fullscreen
- **Fullscreen Mode**: Immersive editing experience
- **Save Status Indicators**: Visual feedback for save operations with timestamps
- **Word/Character Count**: Real-time statistics display

### Technical Features
- **TypeScript**: Full type safety with comprehensive interfaces
- **React Hooks**: Modern React patterns with custom hooks for reusability
- **Tailwind CSS**: Consistent styling with the existing design system
- **Component Patterns**: Follows established patterns from ChatMessage/DraftsModal
- **Error Handling**: Graceful error states and user feedback
- **Performance**: Optimized debouncing and cleanup

## Installation & Setup

The component is self-contained and ready to use. No additional dependencies are required beyond the existing project dependencies.

### Dependencies
- React 18+
- TypeScript
- Tailwind CSS
- Existing MarkdownRenderer component
- IndexedDB (browser native)

## Usage

### Basic Usage

```tsx
import LessonEditor from './components/unified/LessonEditor';

function MyComponent() {
  const [content, setContent] = useState('# My Lesson\n\nContent here...');
  
  const handleSave = async (newContent: string) => {
    // Save to your backend
    await fetch('/api/lessons', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newContent })
    });
    setContent(newContent);
  };
  
  const handleCancel = () => {
    // Handle cancel action
    console.log('Editing cancelled');
  };
  
  return (
    <LessonEditor
      content={content}
      onSave={handleSave}
      onCancel={handleCancel}
      autoSave={true}
    />
  );
}
```

### Props Interface

```tsx
interface LessonEditorProps {
  content: string;           // Initial markdown content
  onSave: (content: string) => Promise<void>; // Save callback
  onCancel: () => void;      // Cancel callback
  autoSave?: boolean;        // Enable/disable auto-save (default: true)
}
```

## View Modes

### Edit Mode
- Full-width markdown textarea
- Monospace font for better code formatting
- Auto-focus on mount
- Real-time character/word count

### Preview Mode
- Full-width rendered markdown
- Uses existing MarkdownRenderer component
- Consistent styling with the rest of the application

### Split Mode
- 50/50 split between editor and preview
- Synchronized scrolling (can be implemented)
- Ideal for iterative editing

## Auto-Save System

### Debounce Logic
- **Immediate**: Triggers after 2 seconds of no typing
- **Periodic**: Saves every 30 seconds regardless of activity
- **Manual**: Ctrl+S or Save button for immediate saving

### Recovery System
- Automatically saves to IndexedDB alongside backend saves
- Recovers unsaved changes on page refresh
- User confirmation dialog for recovery
- Graceful fallback if IndexedDB unavailable

### Save Status Indicators
- **Saving...**: Blue text during save operations
- **Saved**: Green text with timestamp
- **Unsaved changes**: Orange text when there are pending changes
- **Save failed**: Red text for error states

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S (or Cmd+S) | Immediate save |
| Esc | Exit fullscreen or cancel editing |

## Styling & Design

### CSS Classes
The component uses Tailwind CSS classes for consistent styling:
- `bg-parchment-50`: Light background matching the app theme
- `border-ink-200`: Subtle borders
- `text-ink-800/600/700`: Consistent text colors
- `bg-ink-600`: Primary action buttons
- `hover:bg-ink-700`: Interactive states

### Responsive Design
- Fullscreen mode for immersive editing
- Flexible layouts that adapt to container size
- Mobile-friendly touch targets

## Storage Implementation

### IndexedDB Schema
```tsx
interface LessonEditorStorageItem {
  id: string;        // 'current-lesson' for active editing
  content: string;   // Markdown content
  timestamp: string; // ISO timestamp
}
```

### Storage Operations
- `saveContent(id, content)`: Save content with timestamp
- `loadContent(id)`: Retrieve saved content
- `deleteContent(id)`: Remove specific content
- `clearAllContent()`: Clean up all stored data

## Integration Examples

### With ChatMessage (Inline Editing)
```tsx
function EditableChatMessage({ message }) {
  const [isEditing, setIsEditing] = useState(false);
  
  if (isEditing) {
    return (
      <LessonEditor
        content={message.text}
        onSave={async (content) => {
          await updateMessage(message.id, content);
          setIsEditing(false);
        }}
        onCancel={() => setIsEditing(false)}
      />
    );
  }
  
  return <ChatMessage message={message} onEdit={() => setIsEditing(true)} />;
}
```

### With DraftsModal (Standalone Editing)
```tsx
function DraftsModal() {
  const [selectedDraft, setSelectedDraft] = useState(null);
  
  if (selectedDraft) {
    return (
      <LessonEditor
        content={selectedDraft.content}
        onSave={async (content) => {
          await saveDraft(selectedDraft.id, content);
          setSelectedDraft(null);
        }}
        onCancel={() => setSelectedDraft(null)}
      />
    );
  }
  
  // Render draft selection UI
}
```

## Performance Considerations

### Debouncing
- Prevents excessive API calls during typing
- Configurable delay timing
- Cleanup on component unmount

### Memory Management
- Automatic cleanup of timeouts
- IndexedDB connection management
- Event listener cleanup

### Render Optimization
- Conditional rendering based on view mode
- Efficient state updates
- Minimal re-renders with useCallback

## Error Handling

### Save Failures
- Visual error indicators
- Console error logging
- Graceful fallback to local storage

### Recovery Issues
- Silent failures for storage operations
- User-friendly recovery prompts
- Fallback to initial content

## Browser Compatibility

### IndexedDB Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Graceful degradation for unsupported browsers
- Fallback behavior when storage fails

### Feature Detection
```tsx
if ('indexedDB' in window) {
  // Use storage features
} else {
  // Fallback behavior
}
```

## Testing

The component includes comprehensive example usage in `LessonEditor.example.tsx` demonstrating:
- Standalone editing workflow
- Inline editing integration
- Draft system integration
- Error handling scenarios

## Future Enhancements

### Potential Improvements
- Collaborative editing with WebSocket support
- Advanced markdown syntax highlighting
- Image upload integration
- Template system integration
- Export functionality (PDF, DOCX)
- Version history and rollback
- Real-time collaboration indicators

### Extension Points
- Custom save handlers
- Additional view modes
- Plugin system for markdown extensions
- Theme customization
- Localization support

## Troubleshooting

### Common Issues

**Auto-save not working**
- Check if `autoSave` prop is enabled
- Verify IndexedDB availability in browser
- Check console for storage errors

**Content not recovering**
- Ensure IndexedDB permissions are granted
- Check browser storage quota
- Verify recovery logic in useEffect

**Performance issues**
- Monitor debouncing effectiveness
- Check for memory leaks in dev tools
- Verify cleanup of timeouts and event listeners

### Debug Mode
Enable console logging to track:
- Save operations and timing
- Storage operations
- Component lifecycle events

```tsx
// In development, add debug logging
useEffect(() => {
  if (process.env.NODE_ENV === 'development') {
    console.log('LessonEditor mounted with autoSave:', autoSave);
  }
}, [autoSave]);
```

## Contributing

When modifying the LessonEditor component:
1. Maintain TypeScript type safety
2. Follow existing component patterns
3. Update documentation for new features
4. Test with both standalone and inline usage
5. Verify auto-save and recovery functionality
6. Ensure responsive design compatibility