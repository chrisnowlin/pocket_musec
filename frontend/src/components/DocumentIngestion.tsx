import { useState, useCallback } from 'react';
import FileOperationErrorBoundary from './FileOperationErrorBoundary';
import { ingestionService, DocumentClassification, IngestionResults, IngestionResponse } from '../services/ingestionService';
import { useFileValidation } from '../hooks/useFileStorage';
import {
  FileMetadata,
  DuplicateFileWarning,
  formatFileSize,
  formatDate,
  getRelativeTime,
  FILE_STATUS_LABELS
} from '../types/fileStorage';

interface DocumentIngestionProps {
  onIngestionComplete?: (response: IngestionResponse) => void;
}

export default function DocumentIngestion({ onIngestionComplete }: DocumentIngestionProps) {
  const [file, setFile] = useState<File | null>(null);
  const [classification, setClassification] = useState<DocumentClassification | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<'upload' | 'classification' | 'confirm' | 'processing' | 'complete' | 'duplicate'>('upload');
  const [results, setResults] = useState<IngestionResults | null>(null);
  const [fileMetadata, setFileMetadata] = useState<FileMetadata | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<DuplicateFileWarning | null>(null);
  const [error, setError] = useState<string>('');
  const { validateFile } = useFileValidation();

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    // Validate file using the new validation hook
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Additional PDF check for backwards compatibility
    if (!selectedFile.type.includes('pdf')) {
      setError('Please select a PDF file');
      return;
    }

    setError('');
    setFile(selectedFile);
    setIsProcessing(true);
    setCurrentStep('classification');

    try {
      const classificationResult = await ingestionService.classifyDocument(selectedFile);
      setClassification(classificationResult);
      setCurrentStep('confirm');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Classification failed');
      setCurrentStep('upload');
    } finally {
      setIsProcessing(false);
    }
  }, [validateFile]);

  const handleIngestion = useCallback(async () => {
    if (!file) return;

    setIsProcessing(true);
    setCurrentStep('processing');
    setError('');

    try {
      const ingestionResponse = await ingestionService.ingestDocument({
        file
      });
      console.log('Ingestion response:', ingestionResponse);
      
      if (ingestionResponse.duplicate) {
        setDuplicateWarning({
          duplicate: true,
          message: ingestionResponse.message || 'File already exists',
          existing_file: ingestionResponse.existing_file as any
        });
        setCurrentStep('duplicate');
      } else {
        setResults(ingestionResponse.results || null);
        setFileMetadata(ingestionResponse.file_metadata || null);
        setCurrentStep('complete');
        onIngestionComplete?.(ingestionResponse);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed');
      setCurrentStep('confirm');
    } finally {
      setIsProcessing(false);
    }
  }, [file, onIngestionComplete]);

  const handleReset = useCallback(() => {
    setFile(null);
    setClassification(null);
    setResults(null);
    setFileMetadata(null);
    setDuplicateWarning(null);
    setError('');
    setCurrentStep('upload');
    setIsProcessing(false);
  }, []);

  const handleDownloadFile = async (fileId: string, filename: string) => {
    try {
      const blob = await ingestionService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download file');
    }
  };


  const renderResults = useCallback(() => {
    if (!results) return null;

    const metrics = [];

    if (results.standards_count !== undefined) {
      metrics.push({ label: 'Standards Processed', value: results.standards_count, icon: '📋' });
    }
    if (results.objectives_count !== undefined) {
      metrics.push({ label: 'Learning Objectives', value: results.objectives_count, icon: '🎯' });
    }
    if (results.sections_count !== undefined) {
      metrics.push({ label: 'Content Sections', value: results.sections_count, icon: '📚' });
    }
    if (results.strategies_count !== undefined) {
      metrics.push({ label: 'Teaching Strategies', value: results.strategies_count, icon: '💡' });
    }
    if (results.guidance_count !== undefined) {
      metrics.push({ label: 'Assessment Guidance', value: results.guidance_count, icon: '📝' });
    }
    if (results.relationships_count !== undefined) {
      metrics.push({ label: 'Relationships', value: results.relationships_count, icon: '🔗' });
    }
    if (results.mappings_count !== undefined) {
      metrics.push({ label: 'Progression Mappings', value: results.mappings_count, icon: '📈' });
    }
    if (results.glossary_count !== undefined) {
      metrics.push({ label: 'Glossary Entries', value: results.glossary_count, icon: '📖' });
    }
    if (results.faq_count !== undefined) {
      metrics.push({ label: 'FAQ Entries', value: results.faq_count, icon: '❓' });
    }
    if (results.resource_count !== undefined) {
      metrics.push({ label: 'Resource Entries', value: results.resource_count, icon: '🔧' });
    }

    const fileMetrics = [];
    
    if (fileMetadata) {
      fileMetrics.push({
        label: 'File Size',
        value: formatFileSize(fileMetadata.file_size),
        icon: '📁',
        detail: fileMetadata.original_filename
      });
      fileMetrics.push({
        label: 'File ID',
        value: fileMetadata.file_id.substring(0, 8) + '...',
        icon: '🏷️',
        detail: 'Unique identifier'
      });
      fileMetrics.push({
        label: 'Upload Date',
        value: formatDate(fileMetadata.created_at),
        icon: '📅',
        detail: getRelativeTime(fileMetadata.created_at)
      });
      fileMetrics.push({
        label: 'Status',
        value: FILE_STATUS_LABELS[fileMetadata.ingestion_status],
        icon: fileMetadata.ingestion_status === 'completed' ? '✅' :
              fileMetadata.ingestion_status === 'processing' ? '⏳' :
              fileMetadata.ingestion_status === 'error' ? '❌' : '⬆️',
        detail: fileMetadata.ingestion_status
      });
    }

    return (
      <div className="space-y-6 mb-6">
        {/* File Storage Information */}
        {fileMetadata && (
          <div className="workspace-card rounded-lg p-4">
            <h4 className="font-semibold text-ink-800 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-ink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              File Storage Information
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {fileMetrics.map((metric, index) => (
                <div key={index} className="text-center">
                  <div className="text-lg mb-1">{metric.icon}</div>
                  <div className="font-semibold text-ink-700">{metric.value}</div>
                  <div className="text-xs text-ink-600">{metric.label}</div>
                  <div className="text-xs text-ink-500">{metric.detail}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-ink-200">
              <button
                onClick={() => handleDownloadFile(fileMetadata.file_id, fileMetadata.original_filename)}
                className="inline-flex items-center px-3 py-2 border border-ink-300 rounded-md text-sm text-ink-700 hover:bg-parchment-200"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Original File
              </button>
            </div>
          </div>
        )}

        {/* Content Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <div key={index} className="workspace-card rounded-lg p-4 text-center">
              <div className="text-2xl mb-2">{metric.icon}</div>
              <div className="text-2xl font-bold text-ink-700">{metric.value}</div>
              <div className="text-sm text-ink-600">{metric.label}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }, [results, fileMetadata]);

  return (
    <FileOperationErrorBoundary
      onFileError={(error, operation) => {
        console.error(`DocumentIngestion file operation error in ${operation}:`, error);
        setError(`File operation failed during ${operation}: ${error.message}`);
      }}
    >
      <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-ink-800 mb-2">Document Ingestion</h2>
        <p className="text-ink-600">
          Upload and process music education documents with AI-powered analysis
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      {/* Step 1: File Upload */}
      {currentStep === 'upload' && (
        <div className="workspace-card rounded-lg p-6">
          <h3 className="text-lg font-medium text-ink-800 mb-4">Upload Document</h3>
          
          <div className="border-2 border-dashed border-ink-300 rounded-lg p-8 text-center hover:border-ink-400 transition-colors bg-parchment-50">
            <svg className="mx-auto h-12 w-12 text-ink-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            
            <p className="text-ink-700 mb-2">Drop your PDF file here, or click to browse</p>
            <p className="text-sm text-ink-600 mb-4">Supported: NC Music Standards, Unpacking Documents, Alignment Matrices, Reference Materials</p>
            
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-parchment-100 bg-ink-600 hover:bg-ink-700 cursor-pointer"
            >
              Select PDF File
            </label>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="workspace-card rounded-lg p-4">
              <h4 className="font-medium text-ink-800 mb-2">📋 Standards Documents</h4>
              <p className="text-sm text-ink-600">NCSCOS standards, learning objectives, competency frameworks</p>
            </div>
            <div className="workspace-card rounded-lg p-4">
              <h4 className="font-medium text-ink-800 mb-2">📚 Unpacking Documents</h4>
              <p className="text-sm text-ink-600">Grade-level teaching strategies, assessment guidance</p>
            </div>
            <div className="workspace-card rounded-lg p-4">
              <h4 className="font-medium text-ink-800 mb-2">🔗 Alignment Matrices</h4>
              <p className="text-sm text-ink-600">Horizontal/vertical standard relationships, progressions</p>
            </div>
            <div className="workspace-card rounded-lg p-4">
              <h4 className="font-medium text-ink-800 mb-2">📖 Reference Materials</h4>
              <p className="text-sm text-ink-600">Glossaries, FAQs, implementation guides, resources</p>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Classification Results */}
      {currentStep === 'classification' && (
        <div className="workspace-card rounded-lg p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ink-600 mx-auto mb-4"></div>
            <p className="text-ink-600">Analyzing document...</p>
          </div>
        </div>
      )}

      {/* Step 3: Confirmation */}
      {currentStep === 'confirm' && classification && (
        <div className="workspace-card rounded-lg p-6">
          <div className="mb-6">
            <h3 className="text-lg font-medium text-ink-800 mb-4">Document Analysis Results</h3>
            
            <div className="bg-parchment-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-ink-600">File Name</p>
                  <p className="font-medium text-ink-800">{classification.fileName}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-ink-600">Classification</p>
                  <div className="flex items-center justify-end">
                    <span className="text-2xl mr-2">{classification.documentType.icon}</span>
                    <span className="font-medium text-ink-800">{classification.documentType.label}</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-ink-600">Confidence</p>
                  <p className="font-medium text-ink-800">{Math.round(classification.confidence * 100)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-parchment-200 rounded-lg p-4 mb-6 border border-ink-300">
              <p className="text-sm text-ink-700">
                {classification.documentType.description}
              </p>
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={handleReset}
              className="px-4 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200"
            >
              Choose Different File
            </button>
            <div className="space-x-3">
              <button
                onClick={() => setCurrentStep('upload')}
                className="px-4 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200"
              >
                Back
              </button>
              <button
                onClick={handleIngestion}
                disabled={isProcessing}
                className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 disabled:opacity-50"
              >
                {isProcessing ? 'Processing...' : 'Proceed with Ingestion'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Processing */}
      {currentStep === 'processing' && (
        <div className="workspace-card rounded-lg p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ink-600 mx-auto mb-4"></div>
            <p className="text-lg font-medium text-ink-800 mb-2">Processing Document</p>
            <p className="text-ink-600">
              Extracting content and storing in database... This may take a few moments.
            </p>
          </div>
        </div>
      )}

      {/* Step 5: Duplicate File Warning */}
      {currentStep === 'duplicate' && duplicateWarning && (
        <div className="workspace-card rounded-lg p-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 rounded-full mb-4 border border-yellow-300">
              <svg className="w-8 h-8 text-yellow-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-ink-800 mb-2">Duplicate File Detected</h3>
            <p className="text-ink-600">
              This file has already been uploaded and processed.
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-ink-800 mb-2">Existing File Information</h4>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-ink-600">File Name:</span>
                <span className="ml-2 font-medium text-ink-800">{duplicateWarning.existing_file.filename}</span>
              </div>
              <div>
                <span className="text-ink-600">Upload Date:</span>
                <span className="ml-2 font-medium text-ink-800">{formatDate(duplicateWarning.existing_file.upload_date)}</span>
              </div>
              <div>
                <span className="text-ink-600">Status:</span>
                <span className="ml-2 font-medium text-ink-800">{duplicateWarning.existing_file.status}</span>
              </div>
            </div>
          </div>

          <div className="bg-parchment-200 rounded-lg p-4 mb-6 border border-ink-300">
            <p className="text-sm text-ink-700">
              {duplicateWarning.message}
            </p>
          </div>

          <div className="flex justify-center space-x-3">
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
            >
              Upload Different File
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200"
            >
              Go to Workspace
            </button>
          </div>
        </div>
      )}

      {/* Step 6: Complete */}
      {currentStep === 'complete' && (
        <div className="workspace-card rounded-lg p-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-parchment-200 rounded-full mb-4 border border-ink-300">
              <svg className="w-8 h-8 text-ink-700" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-ink-800 mb-2">
              {fileMetadata ? 'File Successfully Stored!' : 'Ingestion Complete!'}
            </h3>
            <p className="text-ink-600">
              {fileMetadata
                ? 'Your document has been successfully processed and permanently stored in the file system.'
                : 'Your document has been successfully processed and stored in the database.'
              }
            </p>
          </div>

          {renderResults()}

          <div className="flex justify-center space-x-3">
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
            >
              Ingest Another Document
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200"
            >
              Go to Workspace
            </button>
          </div>
        </div>
      )}
    </div>
    </FileOperationErrorBoundary>
  );
}