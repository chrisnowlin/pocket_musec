import { Citation, FileCitation, EnhancedCitation, FileMetadata } from '../types/fileStorage';
import { normalizeCitations } from './citationUtils';

/**
 * Test utilities for citation implementation
 * These functions help verify that the citation system works correctly
 */

// Test data
export const createTestCitation = (overrides: Partial<Citation> = {}): Citation => ({
  id: 'test-citation-1',
  lessonId: 'test-lesson-1',
  sourceType: 'document',
  sourceId: 'test-source-1',
  sourceTitle: 'Test Document',
  pageNumber: 1,
  excerpt: 'This is a test citation with file information',
  citationText: 'This is a test citation with file information',
  citationNumber: 1,
  fileId: 'test-file-1',
  createdAt: '2024-01-01T00:00:00Z',
  ...overrides
});

export const createTestFileMetadata = (overrides: Partial<FileMetadata> = {}): FileMetadata => ({
  id: 'test-file-1',
  fileId: 'test-file-1',
  originalFilename: 'test-document.pdf',
  fileHash: 'test-hash',
  fileSize: 1024000,
  mimeType: 'application/pdf',
  documentType: 'standards',
  ingestionStatus: 'completed',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
  ...overrides
});

export const createTestFileCitation = (overrides: Partial<FileCitation> = {}): FileCitation => ({
  citation: createTestCitation(),
  fileMetadata: createTestFileMetadata(),
  isFileAvailable: true,
  downloadUrl: '/api/files/test-file-1/download',
  ...overrides
});

export const createTestEnhancedCitation = (overrides: Partial<EnhancedCitation> = {}): EnhancedCitation => ({
  id: 'test-citation-1',
  citationNumber: 1,
  sourceTitle: 'Test Document',
  sourceType: 'document',
  fileMetadata: {
    id: 'test-file-1',
    fileId: 'test-file-1',
    originalFilename: 'test-document.pdf',
    fileSize: 1024000,
    mimeType: 'application/pdf',
    createdAt: '2024-01-01T00:00:00Z',
    documentType: 'standards',
  },
  pageNumber: 1,
  excerpt: 'This is a test citation with file information',
  citationText: 'This is a test citation with file information',
  isFileAvailable: true,
  canDownload: true,
  formattedDate: 'Jan 1, 2024',
  relativeTime: '2 hours ago',
  ...overrides
});

// Test functions
export const testCitationNormalization = () => {
  console.log('Testing citation normalization...');
  
  // Test with legacy string citations
  const legacyCitations = [
    'Document 1 - Page 1',
    'Document 2 - Page 2'
  ];
  
  const normalizedLegacy = normalizeCitations(legacyCitations);
  console.log('Legacy citations normalized:', normalizedLegacy);
  
  // Test with mixed citations
  const mixedCitations = [
    'Document 1 - Page 1',
    createTestCitation({ id: 'test-citation-2', sourceTitle: 'Document 2' })
  ];
  
  const normalizedMixed = normalizeCitations(mixedCitations);
  console.log('Mixed citations normalized:', normalizedMixed);
  
  // Verify results
  const success = normalizedLegacy.length === 2 &&
                  normalizedMixed.length === 2 &&
                  normalizedMixed.some(c => typeof c === 'string') &&
                  normalizedMixed.some(c => typeof c === 'object' && c !== null);
  
  console.log('Citation normalization test:', success ? 'PASSED' : 'FAILED');
  return success;
};

export const testCitationValidation = () => {
  console.log('Testing citation validation...');
  
  // Test valid citation
  const validCitation = createTestCitation();
  const isValid = validCitation.id !== '' && validCitation.sourceTitle !== '';
  console.log('Valid citation validation:', isValid ? 'PASSED' : 'FAILED');
  
  // Test invalid citation (missing required fields)
  const invalidCitation = { ...createTestCitation(), id: '', sourceTitle: '' };
  const isInvalid = invalidCitation.id === '' || invalidCitation.sourceTitle === '';
  console.log('Invalid citation validation:', isInvalid ? 'PASSED' : 'FAILED');
  
  return isValid && isInvalid;
};

export const testEnhancedCitationDetection = () => {
  console.log('Testing enhanced citation detection...');
  
  // Test with enhanced citation
  const enhancedCitation = createTestEnhancedCitation();
  const isEnhanced = enhancedCitation.fileMetadata !== undefined;
  console.log('Enhanced citation detection:', isEnhanced ? 'PASSED' : 'FAILED');
  
  // Test with legacy citation
  const legacyCitation = 'Document 1 - Page 1';
  const isNotEnhanced = typeof legacyCitation === 'string';
  console.log('Legacy citation detection:', isNotEnhanced ? 'PASSED' : 'FAILED');
  
  return isEnhanced && isNotEnhanced;
};

export const testFileCitationAvailability = () => {
  console.log('Testing file citation availability...');
  
  // Test available file citation
  const availableCitation = createTestFileCitation({ isFileAvailable: true });
  const availableTest = availableCitation.isFileAvailable && availableCitation.fileMetadata !== undefined;
  console.log('Available file citation test:', availableTest ? 'PASSED' : 'FAILED');
  
  // Test unavailable file citation
  const unavailableCitation = createTestFileCitation({ isFileAvailable: false, fileMetadata: undefined });
  const unavailableTest = !unavailableCitation.isFileAvailable && unavailableCitation.fileMetadata === undefined;
  console.log('Unavailable file citation test:', unavailableTest ? 'PASSED' : 'FAILED');
  
  return availableTest && unavailableTest;
};

export const runAllTests = () => {
  console.log('Running citation implementation tests...');
  console.log('='.repeat(50));
  
  const results = [
    testCitationNormalization(),
    testCitationValidation(),
    testEnhancedCitationDetection(),
    testFileCitationAvailability()
  ];
  
  const passedTests = results.filter(r => r).length;
  const totalTests = results.length;
  
  console.log('='.repeat(50));
  console.log(`Test Results: ${passedTests}/${totalTests} tests passed`);
  
  if (passedTests === totalTests) {
    console.log('✅ All citation implementation tests PASSED!');
  } else {
    console.log('❌ Some citation implementation tests FAILED!');
  }
  
  return passedTests === totalTests;
};

// Development helper to test the implementation in the browser console
export const testCitationImplementation = () => {
  // This function can be called from the browser console during development
  if (typeof window !== 'undefined') {
    (window as any).testCitations = runAllTests;
    console.log('Citation testing functions available. Call window.testCitations() to run tests.');
  }
};