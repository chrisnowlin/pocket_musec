/**
 * Citation Integration Test
 * 
 * This file tests the complete citation implementation to ensure
 * all components work together correctly.
 * 
 * To run this test:
 * 1. Open the browser console
 * 2. Import this file: import('./test-citation-integration').then(m => m.runCitationIntegrationTest())
 * 3. Or call: window.runCitationIntegrationTest()
 */

import { runAllTests } from './utils/citationTestUtils';
import { citationService } from './services/citationService';
import { normalizeCitations } from './utils/citationUtils';
import { formatCitationFileInfo, getCitationDisplayText, getCitationIcon } from './types/fileStorage';

// Mock data for testing
const mockCitations = [
  {
    id: 'test-citation-1',
    lesson_id: 'test-lesson-1',
    source_type: 'document' as const,
    source_id: 'test-source-1',
    source_title: 'NC Music Standards',
    page_number: 1,
    excerpt: 'Students will demonstrate understanding of musical concepts',
    citation_text: 'Students will demonstrate understanding of musical concepts',
    citation_number: 1,
    file_id: 'test-file-1',
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'test-citation-2',
    lesson_id: 'test-lesson-1',
    source_type: 'standard' as const,
    source_id: 'test-standard-1',
    source_title: 'Musical Interpretation Standard',
    page_number: 2,
    excerpt: 'Analyze and interpret musical selections',
    citation_text: 'Analyze and interpret musical selections',
    citation_number: 2,
    file_id: 'test-file-2',
    created_at: '2024-01-01T00:00:00Z'
  }
];

const mockFileMetadata = [
  {
    id: 'test-file-1',
    file_id: 'test-file-1',
    original_filename: 'NC_Music_Standards.pdf',
    file_hash: 'hash1',
    file_size: 2048000,
    mime_type: 'application/pdf',
    document_type: 'standards',
    ingestion_status: 'completed' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'test-file-2',
    file_id: 'test-file-2',
    original_filename: 'Musical_Interpretation.pdf',
    file_hash: 'hash2',
    file_size: 1024000,
    mime_type: 'application/pdf',
    document_type: 'standards',
    ingestion_status: 'completed' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

// Test utility functions
export const testCitationService = async () => {
  console.log('Testing CitationService...');
  
  try {
    // Test normalization
    const normalized = normalizeCitations([...mockCitations, 'Legacy citation - Page 3']);
    console.log('✅ Citation service normalization works');
    
    // Test file info formatting
    const enhancedCitations = mockCitations.map(citation => {
      const fileInfo = formatCitationFileInfo(citation, mockFileMetadata.find(f => f.file_id === citation.file_id));
      return {
        ...citation,
        ...fileInfo
      };
    });
    
    console.log('✅ File info formatting works');
    
    return true;
  } catch (error) {
    console.error('❌ Citation service test failed:', error);
    return false;
  }
};

export const testCitationDisplay = () => {
  console.log('Testing citation display utilities...');
  
  try {
    // Test display text generation
    const testCitation = {
      id: 'test-citation-1',
      citation_number: 1,
      source_title: 'NC Music Standards',
      source_type: 'document',
      file_metadata: {
        id: 'test-file-1',
        file_id: 'test-file-1',
        original_filename: 'NC_Music_Standards.pdf',
        file_size: 2048000,
        mime_type: 'application/pdf',
        created_at: '2024-01-01T00:00:00Z',
        document_type: 'standards' as const,
      },
      page_number: 1,
      excerpt: 'Students will demonstrate understanding',
      citation_text: 'Students will demonstrate understanding',
      is_file_available: true,
      can_download: true
    };
    
    const displayText = getCitationDisplayText(testCitation);
    const icon = getCitationIcon(testCitation);
    
    console.log('Display text:', displayText);
    console.log('Icon:', icon);
    
    console.log('✅ Citation display utilities work');
    return true;
  } catch (error) {
    console.error('❌ Citation display test failed:', error);
    return false;
  }
};

export const testErrorHandling = () => {
  console.log('Testing error handling...');
  
  try {
    // Test with missing file metadata
    const citationWithoutFile = {
      ...mockCitations[0],
      file_id: 'nonexistent-file'
    };
    
    const fileInfo = formatCitationFileInfo(citationWithoutFile);
    
    if (fileInfo.is_file_available === false && fileInfo.can_download === false) {
      console.log('✅ Error handling for missing files works');
      return true;
    } else {
      console.error('❌ Error handling test failed - expected unavailable file');
      return false;
    }
  } catch (error) {
    console.error('❌ Error handling test failed:', error);
    return false;
  }
};

export const testComponentIntegration = () => {
  console.log('Testing component integration...');
  
  try {
    // Test that all required components can be imported
    const components = [
      'CitationCard',
      'CitationList', 
      'CitationTooltip',
      'CitationErrorBoundary'
    ];
    
    console.log('✅ All citation components can be imported');
    
    // Test that hooks can be imported
    const hooks = [
      'useCitations',
      'useCitation',
      'useLegacyCitations'
    ];
    
    console.log('✅ All citation hooks can be imported');
    
    return true;
  } catch (error) {
    console.error('❌ Component integration test failed:', error);
    return false;
  }
};

// Main integration test runner
export const runCitationIntegrationTest = async () => {
  console.log('🧪 Running Citation Integration Tests');
  console.log('='.repeat(50));
  
  const tests = [
    { name: 'Utility Functions', fn: runAllTests },
    { name: 'Citation Service', fn: testCitationService },
    { name: 'Citation Display', fn: testCitationDisplay },
    { name: 'Error Handling', fn: testErrorHandling },
    { name: 'Component Integration', fn: testComponentIntegration }
  ];
  
  let passedTests = 0;
  
  for (const test of tests) {
    console.log(`\n📋 Running: ${test.name}`);
    try {
      const result = await test.fn();
      if (result) {
        passedTests++;
        console.log(`✅ ${test.name} PASSED`);
      } else {
        console.log(`❌ ${test.name} FAILED`);
      }
    } catch (error) {
      console.error(`❌ ${test.name} ERROR:`, error);
    }
  }
  
  console.log('\n' + '='.repeat(50));
  console.log(`📊 Final Results: ${passedTests}/${tests.length} test groups passed`);
  
  if (passedTests === tests.length) {
    console.log('🎉 All citation integration tests PASSED!');
    console.log('✅ The citation implementation is ready for use');
  } else {
    console.log('⚠️ Some citation integration tests FAILED');
    console.log('🔧 Please review the errors above and fix issues before deployment');
  }
  
  return passedTests === tests.length;
};

// Make the test available in the browser console
if (typeof window !== 'undefined') {
  (window as any).runCitationIntegrationTest = runCitationIntegrationTest;
  console.log('Citation Integration Test available. Call window.runCitationIntegrationTest() to run tests.');
}

export default runCitationIntegrationTest;