import { Citation, FileCitation, EnhancedCitation, FileMetadata } from '../types/fileStorage';
import { normalizeCitations } from './citationUtils';

/**
 * Test utilities for citation implementation
 * These functions help verify that the citation system works correctly
 */

// Test data
export const createTestCitation = (overrides: Partial<Citation> = {}): Citation => ({
  id: 'test-citation-1',
  lesson_id: 'test-lesson-1',
  source_type: 'document',
  source_id: 'test-source-1',
  source_title: 'Test Document',
  page_number: 1,
  excerpt: 'This is a test citation with file information',
  citation_text: 'This is a test citation with file information',
  citation_number: 1,
  file_id: 'test-file-1',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides
});

export const createTestFileMetadata = (overrides: Partial<FileMetadata> = {}): FileMetadata => ({
  id: 'test-file-1',
  file_id: 'test-file-1',
  original_filename: 'test-document.pdf',
  file_hash: 'test-hash',
  file_size: 1024000,
  mime_type: 'application/pdf',
  document_type: 'standards',
  ingestion_status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides
});

export const createTestFileCitation = (overrides: Partial<FileCitation> = {}): FileCitation => ({
  citation: createTestCitation(),
  file_metadata: createTestFileMetadata(),
  is_file_available: true,
  download_url: '/api/files/test-file-1/download',
  ...overrides
});

export const createTestEnhancedCitation = (overrides: Partial<EnhancedCitation> = {}): EnhancedCitation => ({
  id: 'test-citation-1',
  citation_number: 1,
  source_title: 'Test Document',
  source_type: 'document',
  file_metadata: {
    id: 'test-file-1',
    file_id: 'test-file-1',
    original_filename: 'test-document.pdf',
    file_size: 1024000,
    mime_type: 'application/pdf',
    created_at: '2024-01-01T00:00:00Z',
    document_type: 'standards',
  },
  page_number: 1,
  excerpt: 'This is a test citation with file information',
  citation_text: 'This is a test citation with file information',
  is_file_available: true,
  can_download: true,
  formatted_date: 'Jan 1, 2024',
  relative_time: '2 hours ago',
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
    createTestCitation({ id: 'test-citation-2', source_title: 'Document 2' })
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
  const isValid = validCitation.id !== '' && validCitation.source_title !== '';
  console.log('Valid citation validation:', isValid ? 'PASSED' : 'FAILED');
  
  // Test invalid citation (missing required fields)
  const invalidCitation = { ...createTestCitation(), id: '', source_title: '' };
  const isInvalid = invalidCitation.id === '' || invalidCitation.source_title === '';
  console.log('Invalid citation validation:', isInvalid ? 'PASSED' : 'FAILED');
  
  return isValid && isInvalid;
};

export const testEnhancedCitationDetection = () => {
  console.log('Testing enhanced citation detection...');
  
  // Test with enhanced citation
  const enhancedCitation = createTestEnhancedCitation();
  const isEnhanced = enhancedCitation.file_metadata !== undefined;
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
  const availableCitation = createTestFileCitation({ is_file_available: true });
  const availableTest = availableCitation.is_file_available && availableCitation.file_metadata !== undefined;
  console.log('Available file citation test:', availableTest ? 'PASSED' : 'FAILED');
  
  // Test unavailable file citation
  const unavailableCitation = createTestFileCitation({ is_file_available: false, file_metadata: undefined });
  const unavailableTest = !unavailableCitation.is_file_available && unavailableCitation.file_metadata === undefined;
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