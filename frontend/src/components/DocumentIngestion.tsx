import { useState, useCallback, useEffect } from 'react';
import { ingestionService, DocumentClassification, IngestionResults } from '../services/ingestionService';

interface DocumentIngestionProps {
  onIngestionComplete?: (results: IngestionResults) => void;
}

export default function DocumentIngestion({ onIngestionComplete }: DocumentIngestionProps) {
  const [file, setFile] = useState<File | null>(null);
  const [classification, setClassification] = useState<DocumentClassification | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<'upload' | 'classification' | 'options' | 'processing' | 'complete'>('upload');
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [results, setResults] = useState<IngestionResults | null>(null);
  const [error, setError] = useState<string>('');
  const [advancedOptions, setAdvancedOptions] = useState<Array<{ id: string; label: string; description: string }>>([]);

  const handleFileSelect = useCallback(async (selectedFile: File) => {
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
      setCurrentStep('options');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Classification failed');
      setCurrentStep('upload');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleAdvancedOption = useCallback((option: string) => {
    setSelectedOption(option);
  }, []);

  const handleIngestion = useCallback(async () => {
    if (!file) return;

    setIsProcessing(true);
    setCurrentStep('processing');
    setError('');

    try {
      const ingestionResults = await ingestionService.ingestDocument({ 
        file, 
        advancedOption: selectedOption 
      });
      setResults(ingestionResults);
      setCurrentStep('complete');
      onIngestionComplete?.(ingestionResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed');
      setCurrentStep('options');
    } finally {
      setIsProcessing(false);
    }
  }, [file, selectedOption, onIngestionComplete]);

  const handleReset = useCallback(() => {
    setFile(null);
    setClassification(null);
    setSelectedOption('');
    setResults(null);
    setError('');
    setCurrentStep('upload');
    setIsProcessing(false);
    setAdvancedOptions([]);
  }, []);

  // Fetch advanced options when classification changes
  useEffect(() => {
    const fetchAdvancedOptions = async () => {
      if (!classification) return;

      try {
        const options = await ingestionService.getAdvancedOptions(classification.documentType.value);
        const formattedOptions = options.map((option, index) => ({
          id: `option-${index}`,
          label: option,
          description: option
        }));
        setAdvancedOptions(formattedOptions);
      } catch (err) {
        console.error('Failed to fetch advanced options:', err);
        // Fallback to default options
        setAdvancedOptions([
          { id: 'default', label: 'Standard Processing', description: 'Default extraction settings' }
        ]);
      }
    };

    fetchAdvancedOptions();
  }, [classification]);

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

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {metrics.map((metric, index) => (
          <div key={index} className="workspace-card rounded-lg p-4 text-center">
            <div className="text-2xl mb-2">{metric.icon}</div>
            <div className="text-2xl font-bold text-ink-700">{metric.value}</div>
            <div className="text-sm text-ink-600">{metric.label}</div>
          </div>
        ))}
      </div>
    );
  }, [results]);

  return (
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

      {/* Step 3: Advanced Options */}
      {currentStep === 'options' && classification && (
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
              <p className="text-sm text-ink-800">
                <strong>Recommended Parser:</strong> {classification.recommendedParser}
              </p>
              <p className="text-sm text-ink-700 mt-1">
                {classification.documentType.description}
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-md font-medium text-ink-800 mb-3">Advanced Options</h4>
            <div className="space-y-3">
              {advancedOptions.map((option) => (
                <label
                  key={option.id}
                  className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedOption === option.id
                      ? 'border-ink-500 bg-parchment-200'
                      : 'border-ink-300 hover:border-ink-400 bg-parchment-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="advanced-option"
                    value={option.id}
                    checked={selectedOption === option.id}
                    onChange={(e) => handleAdvancedOption(e.target.value)}
                    className="mt-1 mr-3 text-ink-600 focus:ring-ink-500"
                  />
                  <div>
                    <div className="font-medium text-ink-800">{option.label}</div>
                    <div className="text-sm text-ink-600">{option.description}</div>
                  </div>
                </label>
              ))}
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
                {isProcessing ? 'Processing...' : 'Start Ingestion'}
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

      {/* Step 5: Complete */}
      {currentStep === 'complete' && (
        <div className="workspace-card rounded-lg p-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-parchment-200 rounded-full mb-4 border border-ink-300">
              <svg className="w-8 h-8 text-ink-700" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-ink-800 mb-2">Ingestion Complete!</h3>
            <p className="text-ink-600">
              Your document has been successfully processed and stored in the database.
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
  );
}