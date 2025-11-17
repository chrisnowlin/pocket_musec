import { useState, useEffect, useCallback } from 'react';
import {
  embeddingsService,
  EmbeddingStats,
  EmbeddingGenerateRequest,
  SemanticSearchRequest,
  SemanticSearchResult,
  SemanticSearchResponse,
  GenerationProgress,
  UsageStats,
  BatchOperationRequest,
  BatchOperationResponse
} from '../services/embeddingsService';
import VirtualScroller from './VirtualScroller';

interface EmbeddingsManagerProps {
  className?: string;
}

export default function EmbeddingsManager({ className = '' }: EmbeddingsManagerProps) {
  const [stats, setStats] = useState<EmbeddingStats | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress>({
    status: 'idle',
    progress: 0,
    message: ''
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[]>([]);
  const [searchResponse, setSearchResponse] = useState<SemanticSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'stats' | 'generate' | 'search' | 'usage' | 'batch'>('stats');
  const [batchOperation, setBatchOperation] = useState<'regenerate' | 'delete' | 'refresh'>('regenerate');
  const [batchInProgress, setBatchInProgress] = useState(false);
  const [useVirtualScroll, setUseVirtualScroll] = useState(false);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [searchRequest, setSearchRequest] = useState<SemanticSearchRequest>({
    query: '',
    gradeLevel: '',
    strandCode: '',
    limit: 50, // Increased limit for virtual scrolling
    threshold: 0.5,
    offset: 0
  });

  // Load stats on component mount
  useEffect(() => {
    loadStats();
    loadUsageStats();
  }, []);

  const loadStats = useCallback(async (forceRefresh: boolean = false) => {
    try {
      const embeddingStats = await embeddingsService.getEmbeddingStats(forceRefresh);
      setStats(embeddingStats);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load embedding stats');
    }
  }, []);

  const loadUsageStats = useCallback(async () => {
    try {
      const stats = await embeddingsService.getUsageStats();
      setUsageStats(stats);
    } catch (err) {
      console.warn('Failed to load usage stats:', err);
      // Don't set error for usage stats as it's not critical
    }
  }, []);

  const handleGenerateEmbeddings = useCallback(async (force: boolean = false) => {
    if (isGenerating) return;
    
    setIsGenerating(true);
    setError('');
    
    try {
      const request: EmbeddingGenerateRequest = {
        force,
        batch_size: 10
      };
      
      const result = await embeddingsService.generateEmbeddingsWithProgress(request, (progress) => {
        setGenerationProgress(progress);
        if (progress.status === 'completed' || progress.status === 'error') {
          setIsGenerating(false);
          loadStats(true); // Force refresh stats after completion
        }
      });
      
      // Track generation usage after completion
      await embeddingsService.trackGenerationUsage(result.success, result.failed, result.skipped);
      await loadUsageStats(); // Refresh usage stats after tracking
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate embeddings');
      setIsGenerating(false);
      setGenerationProgress({ status: 'error', progress: 0, message: 'Generation failed' });
    }
  }, [isGenerating, loadStats, loadUsageStats]);

  const handleSearch = useCallback(async () => {
    if (!searchRequest.query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setIsSearching(true);
    setError('');
    
    try {
      const response = await embeddingsService.semanticSearch(searchRequest);
      setSearchResponse(response);
      setSearchResults(response.results);
      
      // Track search usage
      await embeddingsService.trackSearchUsage(searchRequest.query, response.results.length);
      await loadUsageStats(); // Refresh usage stats after tracking
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setSearchResults([]);
      setSearchResponse(null);
    } finally {
      setIsSearching(false);
    }
  }, [searchRequest, loadUsageStats]);

  const handleClearEmbeddings = useCallback(async () => {
    if (!confirm('Are you sure you want to delete all embeddings? This action cannot be undone.')) {
      return;
    }
    
    try {
      await embeddingsService.clearEmbeddings();
      await loadStats(true); // Force refresh stats after clearing
      await loadUsageStats(); // Refresh usage stats after clearing
      setSearchResults([]);
      setSearchResponse(null);
      setGenerationProgress({ status: 'idle', progress: 0, message: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear embeddings');
    }
  }, [loadStats, loadUsageStats]);

  const handleBatchOperation = useCallback(async (operation: 'regenerate' | 'delete' | 'refresh') => {
    if (batchInProgress || isGenerating) return;
    
    setBatchInProgress(true);
    setError('');
    
    // Show confirmation for destructive operations
    if (operation === 'delete' || operation === 'regenerate') {
      const message = operation === 'delete'
        ? 'Are you sure you want to delete all embeddings? This action cannot be undone.'
        : 'Are you sure you want to regenerate all embeddings? This will replace existing embeddings.';
      
      if (!confirm(message)) {
        setBatchInProgress(false);
        return;
      }
    }
    
    try {
      const request: BatchOperationRequest = {
        operation
      };
      
      const result = await embeddingsService.executeBatchOperationWithProgress(request, (progress) => {
        setGenerationProgress(progress);
        if (progress.status === 'completed' || progress.status === 'error') {
          setBatchInProgress(false);
          loadStats(true); // Force refresh stats after completion
          loadUsageStats(); // Refresh usage stats
        }
      });
      
      // Track generation usage if this was a regeneration operation
      if (operation === 'regenerate') {
        await embeddingsService.trackGenerationUsage(result.success, result.failed, result.skipped);
        await loadUsageStats(); // Refresh usage stats after tracking
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Batch ${operation} failed`);
      setBatchInProgress(false);
      setGenerationProgress({ status: 'error', progress: 0, message: `Batch ${operation} failed` });
    }
  }, [batchInProgress, isGenerating, loadStats, loadUsageStats]);

  const renderStatsTab = () => (
    <div className="space-y-6">
      {stats ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="workspace-card rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-ink-700 mb-2">{stats.standard_embeddings}</div>
              <div className="text-sm text-ink-600">Standard Embeddings</div>
            </div>
            <div className="workspace-card rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-ink-700 mb-2">{stats.objective_embeddings}</div>
              <div className="text-sm text-ink-600">Objective Embeddings</div>
            </div>
            <div className="workspace-card rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-ink-700 mb-2">{stats.embedding_dimension}</div>
              <div className="text-sm text-ink-600">Embedding Dimension</div>
            </div>
          </div>
          
          {stats.standard_embeddings === 0 && (
            <div className="bg-parchment-200 border border-ink-300 rounded-md p-4">
              <p className="text-ink-700 text-center">
                No embeddings found. Generate embeddings to enable semantic search functionality.
              </p>
            </div>
          )}
          
          {/* Export Controls */}
          <div className="workspace-card rounded-lg p-6">
            <h3 className="text-lg font-medium text-ink-800 mb-4">Export Statistics</h3>
            <p className="text-ink-600 mb-4">
              Download embedding statistics for analysis or reporting.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => embeddingsService.exportStatsAsCSV().catch(err => setError(err.message))}
                className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
                aria-label="Export embedding statistics as CSV file"
              >
                Export as CSV
              </button>
              <button
                onClick={() => embeddingsService.exportStatsAsJSON().catch(err => setError(err.message))}
                className="px-4 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200"
                aria-label="Export embedding statistics as JSON file"
              >
                Export as JSON
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center text-ink-600">Loading statistics...</div>
      )}
    </div>
  );

  const renderGenerateTab = () => (
    <div className="space-y-6">
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4" role="alert">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      {isGenerating && (
        <div className="workspace-card rounded-lg p-6">
          <h3 className="text-lg font-medium text-ink-800 mb-4">Generation Progress</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-ink-600">Status:</span>
              <span className={`font-medium ${
                generationProgress.status === 'completed' ? 'text-ink-700' :
                generationProgress.status === 'error' ? 'text-red-600' :
                'text-ink-600'
              }`}>
                {generationProgress.status.charAt(0).toUpperCase() + generationProgress.status.slice(1)}
              </span>
            </div>
            <div className="w-full bg-parchment-200 rounded-full h-2">
              <div 
                className="bg-ink-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${generationProgress.progress}%` }}
              ></div>
            </div>
            <div className="text-sm text-ink-600 text-center">
              {generationProgress.message}
            </div>
          </div>
        </div>
      )}

      <div className="workspace-card rounded-lg p-6">
        <h3 className="text-lg font-medium text-ink-800 mb-4">Generate Embeddings</h3>
        <p className="text-ink-600 mb-6">
          Create semantic embeddings for all standards and objectives to enable intelligent search and recommendations.
        </p>
        
        <div className="space-y-4">
          {stats && stats.standard_embeddings > 0 && (
            <div className="bg-parchment-200 border border-ink-300 rounded-md p-4">
              <p className="text-ink-700">
                Found {stats.standard_embeddings} existing standard embeddings and {stats.objective_embeddings} objective embeddings.
              </p>
            </div>
          )}
          
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => handleGenerateEmbeddings(false)}
              disabled={isGenerating}
              className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 disabled:opacity-50"
            >
              {isGenerating ? 'Generating...' : 'Generate New Embeddings'}
            </button>
            
            {stats && stats.standard_embeddings > 0 && (
              <button
                onClick={() => handleGenerateEmbeddings(true)}
                disabled={isGenerating}
                className="px-6 py-2 border border-ink-300 rounded-md text-ink-700 hover:bg-parchment-200 disabled:opacity-50"
              >
                {isGenerating ? 'Generating...' : 'Regenerate All'}
              </button>
            )}
            
            {stats && stats.standard_embeddings > 0 && (
              <button
                onClick={handleClearEmbeddings}
                disabled={isGenerating}
                className="px-6 py-2 border border-red-300 rounded-md text-red-700 hover:bg-red-50 disabled:opacity-50"
              >
                Clear All Embeddings
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderUsageTab = () => (
    <div className="space-y-6">
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4" role="alert">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      {usageStats ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="workspace-card rounded-lg p-6">
              <h3 className="text-lg font-medium text-ink-800 mb-4">Search Operations</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">Total Searches:</span>
                  <span className="text-sm font-medium text-ink-800">{usageStats.total_searches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">This Week:</span>
                  <span className="text-sm font-medium text-ink-800">{usageStats.searches_this_week}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">Last Search:</span>
                  <span className="text-sm font-medium text-ink-800">
                    {usageStats.last_search ? new Date(usageStats.last_search).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>

            <div className="workspace-card rounded-lg p-6">
              <h3 className="text-lg font-medium text-ink-800 mb-4">Generation Operations</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">Total Generations:</span>
                  <span className="text-sm font-medium text-ink-800">{usageStats.total_generations}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">This Week:</span>
                  <span className="text-sm font-medium text-ink-800">{usageStats.generations_this_week}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-ink-600">Last Generation:</span>
                  <span className="text-sm font-medium text-ink-800">
                    {usageStats.last_generation ? new Date(usageStats.last_generation).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="workspace-card rounded-lg p-6">
            <h3 className="text-lg font-medium text-ink-800 mb-4">Activity Summary</h3>
            <div className="space-y-4">
              <div className="text-sm text-ink-600">
                <p>
                  Usage tracking helps monitor how often embeddings are searched and generated.
                  This data is used to optimize performance and plan system improvements.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="text-center p-4 bg-parchment-100 rounded-lg">
                  <div className="text-2xl font-bold text-ink-700">
                    {usageStats.searches_this_week}
                  </div>
                  <div className="text-sm text-ink-600">Searches this week</div>
                </div>
                <div className="text-center p-4 bg-parchment-100 rounded-lg">
                  <div className="text-2xl font-bold text-ink-700">
                    {usageStats.generations_this_week}
                  </div>
                  <div className="text-sm text-ink-600">Generations this week</div>
                </div>
              </div>
            </div>
            
            {/* Export Controls */}
            <div className="workspace-card rounded-lg p-6">
              <h3 className="text-lg font-medium text-ink-800 mb-4">Export Usage Data</h3>
              <p className="text-ink-600 mb-4">
                Download usage statistics for analysis or reporting.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => embeddingsService.exportUsageAsCSV().catch(err => setError(err.message))}
                  className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
                  aria-label="Export usage statistics as CSV file"
                >
                  Export Usage as CSV
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center text-ink-600">Loading usage statistics...</div>
      )}
    </div>
  );

  const renderBatchTab = () => (
    <div className="space-y-6">
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4" role="alert">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      {(batchInProgress || isGenerating) && generationProgress.status !== 'idle' && (
        <div className="workspace-card rounded-lg p-6">
          <h3 className="text-lg font-medium text-ink-800 mb-4">Batch Operation Progress</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-ink-600">Status:</span>
              <span className={`font-medium ${
                generationProgress.status === 'completed' ? 'text-ink-700' :
                generationProgress.status === 'error' ? 'text-red-600' :
                'text-ink-600'
              }`}>
                {generationProgress.status.charAt(0).toUpperCase() + generationProgress.status.slice(1)}
              </span>
            </div>
            <div className="w-full bg-parchment-200 rounded-full h-2">
              <div
                className="bg-ink-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${generationProgress.progress}%` }}
              ></div>
            </div>
            <div className="text-sm text-ink-600 text-center">
              {generationProgress.message}
            </div>
          </div>
        </div>
      )}

      <div className="workspace-card rounded-lg p-6">
        <h3 className="text-lg font-medium text-ink-800 mb-4">Batch Operations</h3>
        <p className="text-ink-600 mb-6">
          Perform bulk operations on embeddings. These operations will affect all embeddings in the system.
        </p>
        
        <div className="space-y-6">
          <div>
            <label htmlFor="batch-operation" className="block text-sm font-medium text-ink-700 mb-2">
              Select Operation
            </label>
            <select
              id="batch-operation"
              value={batchOperation}
              onChange={(e) => setBatchOperation(e.target.value as 'regenerate' | 'delete' | 'refresh')}
              className="w-full px-3 py-2 border border-ink-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ink-500"
              aria-describedby="batch-operation-help"
              disabled={batchInProgress || isGenerating}
            >
              <option value="regenerate">Regenerate All Embeddings</option>
              <option value="delete">Delete All Embeddings</option>
              <option value="refresh">Refresh Embedding Cache</option>
            </select>
            <p id="batch-operation-help" className="mt-1 text-sm text-ink-600">
              Choose the batch operation to perform on all embeddings
            </p>
          </div>
          
          <div className="bg-parchment-100 border border-ink-200 rounded-md p-4">
            <h4 className="text-sm font-medium text-ink-800 mb-2">Operation Details:</h4>
            {batchOperation === 'regenerate' && (
              <div className="text-sm text-ink-600">
                <p className="mb-2">• Deletes all existing embeddings</p>
                <p className="mb-2">• Generates fresh embeddings for all standards and objectives</p>
                <p>• May take several minutes to complete</p>
              </div>
            )}
            {batchOperation === 'delete' && (
              <div className="text-sm text-ink-600">
                <p className="mb-2">• Permanently deletes all embeddings</p>
                <p className="mb-2">• Disables semantic search functionality</p>
                <p>• This action cannot be undone</p>
              </div>
            )}
            {batchOperation === 'refresh' && (
              <div className="text-sm text-ink-600">
                <p className="mb-2">• Refreshes embedding cache and indices</p>
                <p className="mb-2">• Optimizes search performance</p>
                <p>• Does not modify existing embeddings</p>
              </div>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => handleBatchOperation(batchOperation)}
              disabled={batchInProgress || isGenerating}
              className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 disabled:opacity-50"
              aria-describedby="batch-status"
            >
              {batchInProgress ? `Executing ${batchOperation}...` : `Execute ${batchOperation}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSearchTab = () => (
    <div className="space-y-6">
      {error && (
        <div className="bg-parchment-300 border border-ink-500 rounded-md p-4" role="alert">
          <div className="flex">
            <svg className="h-5 w-5 text-ink-700 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-ink-800">{error}</p>
          </div>
        </div>
      )}

      <div className="workspace-card rounded-lg p-6">
        <h3 className="text-lg font-medium text-ink-800 mb-4">Semantic Search</h3>
        
        <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }} className="space-y-4">
          <div>
            <label htmlFor="search-query" className="block text-sm font-medium text-ink-700 mb-2">
              Search Query
            </label>
            <textarea
              id="search-query"
              value={searchRequest.query}
              onChange={(e) => setSearchRequest({ ...searchRequest, query: e.target.value })}
              placeholder="Enter natural language search query..."
              className="w-full px-3 py-2 border border-ink-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent"
              rows={3}
              aria-describedby="search-query-help"
              aria-required="true"
            />
            <p id="search-query-help" className="mt-1 text-sm text-ink-600">
              Enter keywords or phrases to find related standards
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="grade-level" className="block text-sm font-medium text-ink-700 mb-2">
                Grade Level (Optional)
              </label>
              <input
                id="grade-level"
                type="text"
                value={searchRequest.gradeLevel || ''}
                onChange={(e) => setSearchRequest({ ...searchRequest, gradeLevel: e.target.value })}
                placeholder="e.g., Kindergarten, Grade 1"
                className="w-full px-3 py-2 border border-ink-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ink-500"
                aria-describedby="grade-level-help"
              />
              <p id="grade-level-help" className="mt-1 text-sm text-ink-600">
                Filter by specific grade level
              </p>
            </div>
            
            <div>
              <label htmlFor="strand-code" className="block text-sm font-medium text-ink-700 mb-2">
                Strand Code (Optional)
              </label>
              <input
                id="strand-code"
                type="text"
                value={searchRequest.strandCode || ''}
                onChange={(e) => setSearchRequest({ ...searchRequest, strandCode: e.target.value })}
                placeholder="e.g., M, MH, MR"
                className="w-full px-3 py-2 border border-ink-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ink-500"
                aria-describedby="strand-code-help"
              />
              <p id="strand-code-help" className="mt-1 text-sm text-ink-600">
                Filter by musical strand or category
              </p>
            </div>
            
            <div>
              <label htmlFor="similarity-threshold" className="block text-sm font-medium text-ink-700 mb-2">
                Similarity Threshold
              </label>
              <input
                id="similarity-threshold"
                type="number"
                min="0.1"
                max="1.0"
                step="0.1"
                value={searchRequest.threshold || 0.5}
                onChange={(e) => setSearchRequest({ ...searchRequest, threshold: parseFloat(e.target.value) || 0.5 })}
                className="w-full px-3 py-2 border border-ink-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ink-500"
                aria-describedby="similarity-threshold-help"
              />
              <p id="similarity-threshold-help" className="mt-1 text-sm text-ink-600">
                Minimum similarity score (0.1-1.0)
              </p>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-ink-600" role="status" aria-live="polite">
              {searchResponse ? (
                <>Showing {searchResponse.results.length} of {searchResponse.total_count} results</>
              ) : (
                <>Results: {searchRequest.limit || 10} max</>
              )}
            </div>
            <button
              type="submit"
              disabled={isSearching || !searchRequest.query.trim()}
              className="px-6 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 disabled:opacity-50"
              aria-describedby="search-status"
            >
              {isSearching ? 'Searching...' : 'Search Standards'}
            </button>
          </div>
        </form>
          
          {/* Pagination Controls */}
          {searchResponse && searchRequest.limit && searchResponse.total_count > searchRequest.limit && (
            <div className="flex items-center justify-center space-x-2 mt-4" role="navigation" aria-label="Search results pagination">
              <button
                onClick={() => {
                  const newOffset = Math.max(0, searchRequest.offset! - searchRequest.limit!);
                  setSearchRequest({
                    ...searchRequest,
                    offset: newOffset
                  });
                  // Trigger search with new offset
                  setTimeout(() => {
                    const updatedRequest = { ...searchRequest, offset: newOffset };
                    embeddingsService.semanticSearch(updatedRequest).then(response => {
                      setSearchResponse(response);
                      setSearchResults(response.results);
                    });
                  }, 0);
                }}
                disabled={!searchResponse.has_previous}
                aria-label="Go to previous page"
                className="px-3 py-1 border border-ink-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-parchment-200"
              >
                Previous
              </button>
              
              <span className="text-sm text-ink-600" aria-live="polite">
                Page {Math.floor(searchRequest.offset! / searchRequest.limit!) + 1} of {Math.ceil(searchResponse.total_count / searchRequest.limit!)}
              </span>
              
              <button
                onClick={() => {
                  const newOffset = searchRequest.offset! + searchRequest.limit!;
                  setSearchRequest({
                    ...searchRequest,
                    offset: newOffset
                  });
                  // Trigger search with new offset
                  setTimeout(() => {
                    const updatedRequest = { ...searchRequest, offset: newOffset };
                    embeddingsService.semanticSearch(updatedRequest).then(response => {
                      setSearchResponse(response);
                      setSearchResults(response.results);
                    });
                  }, 0);
                }}
                disabled={!searchResponse.has_next}
                aria-label="Go to next page"
                className="px-3 py-1 border border-ink-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-parchment-200"
              >
                Next
              </button>
            </div>
          )}
      </div>

      {searchResults.length > 0 && (
        <div className="workspace-card rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-ink-800">
              Search Results ({searchResponse ? `${searchResponse.results.length} of ${searchResponse.total_count}` : searchResults.length})
            </h3>
            {searchResults.length > 20 && (
              <div className="flex items-center gap-2">
                <label htmlFor="virtual-scroll-toggle" className="text-sm text-ink-600">
                  Virtual Scrolling:
                </label>
                <button
                  id="virtual-scroll-toggle"
                  onClick={() => setUseVirtualScroll(!useVirtualScroll)}
                  className={`px-3 py-1 text-sm rounded-md border ${
                    useVirtualScroll
                      ? 'bg-ink-600 text-parchment-100 border-ink-600'
                      : 'bg-parchment-100 text-ink-700 border-ink-300 hover:bg-parchment-200'
                  }`}
                  aria-pressed={useVirtualScroll}
                >
                  {useVirtualScroll ? 'On' : 'Off'}
                </button>
              </div>
            )}
          </div>
          
          {useVirtualScroll && searchResults.length > 0 ? (
            <VirtualScroller
              items={searchResults}
              itemHeight={180}
              containerHeight={600}
              renderItem={(result, index) => (
                <div
                  className="border border-ink-200 rounded-lg p-4 mx-2 my-2 hover:bg-parchment-50 focus-within:ring-2 focus-within:ring-ink-500"
                  role="listitem"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      // Could expand to show more details or navigate to full standard
                    }
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-ink-700" aria-label={`Grade level: ${result.gradeLevel}`}>
                          {result.gradeLevel}
                        </span>
                        <span className="text-sm text-ink-500" aria-hidden="true">•</span>
                        <span className="text-sm text-ink-700" aria-label={`Strand: ${result.strandCode} - ${result.strandName}`}>
                          {result.strandCode} - {result.strandName}
                        </span>
                      </div>
                      <div className="text-sm font-medium text-ink-800 mb-2" aria-label={`Standard ID: ${result.standard_id}`}>
                        {result.standard_id}
                      </div>
                      <p className="text-ink-600 text-sm leading-relaxed" aria-label="Standard description">
                        {result.standard_text}
                      </p>
                    </div>
                    <div className="ml-4 text-right">
                      <div className="text-sm font-medium text-ink-700">
                        Similarity
                      </div>
                      <div
                        className={`text-lg font-bold ${
                          result.similarity > 0.8 ? 'text-ink-700' :
                          result.similarity > 0.6 ? 'text-ink-600' :
                          'text-ink-500'
                        }`}
                        aria-label={`Similarity score: ${(result.similarity * 100).toFixed(1)}%`}
                      >
                        {result.similarity.toFixed(3)}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              className="border border-ink-200 rounded-md"
            />
          ) : (
            <div className="space-y-4" role="list" aria-label="Search results">
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  className="border border-ink-200 rounded-lg p-4 hover:bg-parchment-50 focus-within:ring-2 focus-within:ring-ink-500"
                  role="listitem"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      // Could expand to show more details or navigate to full standard
                    }
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-ink-700" aria-label={`Grade level: ${result.gradeLevel}`}>
                          {result.gradeLevel}
                        </span>
                        <span className="text-sm text-ink-500" aria-hidden="true">•</span>
                        <span className="text-sm text-ink-700" aria-label={`Strand: ${result.strandCode} - ${result.strandName}`}>
                          {result.strandCode} - {result.strandName}
                        </span>
                      </div>
                      <div className="text-sm font-medium text-ink-800 mb-2" aria-label={`Standard ID: ${result.standard_id}`}>
                        {result.standard_id}
                      </div>
                      <p className="text-ink-600 text-sm leading-relaxed" aria-label="Standard description">
                        {result.standard_text}
                      </p>
                    </div>
                    <div className="ml-4 text-right">
                      <div className="text-sm font-medium text-ink-700">
                        Similarity
                      </div>
                      <div
                        className={`text-lg font-bold ${
                          result.similarity > 0.8 ? 'text-ink-700' :
                          result.similarity > 0.6 ? 'text-ink-600' :
                          'text-ink-500'
                        }`}
                        aria-label={`Similarity score: ${(result.similarity * 100).toFixed(1)}%`}
                      >
                        {result.similarity.toFixed(3)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className={`max-w-6xl mx-auto space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center" role="banner">
        <h2 className="text-2xl font-bold text-ink-800 mb-2">Embeddings Manager</h2>
        <p className="text-ink-600">
          Generate and manage semantic embeddings for intelligent standards search
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-ink-200" role="tablist" aria-label="Embeddings management sections">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('stats')}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const tabs = ['stats', 'generate', 'search', 'usage', 'batch'];
                const currentIndex = tabs.indexOf(activeTab);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                  newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                  newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                setActiveTab(tabs[newIndex] as 'stats' | 'generate' | 'search' | 'usage' | 'batch');
              }
            }}
            role="tab"
            aria-selected={activeTab === 'stats'}
            aria-controls="stats-panel"
            id="stats-tab"
            tabIndex={activeTab === 'stats' ? 0 : -1}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-ink-500 text-ink-700'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Statistics
          </button>
          <button
            onClick={() => setActiveTab('generate')}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const tabs = ['stats', 'generate', 'search', 'usage', 'batch'];
                const currentIndex = tabs.indexOf(activeTab);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                  newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                  newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                setActiveTab(tabs[newIndex] as 'stats' | 'generate' | 'search' | 'usage' | 'batch');
              }
            }}
            role="tab"
            aria-selected={activeTab === 'generate'}
            aria-controls="generate-panel"
            id="generate-tab"
            tabIndex={activeTab === 'generate' ? 0 : -1}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'generate'
                ? 'border-ink-500 text-ink-700'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Generate
          </button>
          <button
            onClick={() => setActiveTab('search')}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const tabs = ['stats', 'generate', 'search', 'usage', 'batch'];
                const currentIndex = tabs.indexOf(activeTab);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                  newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                  newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                setActiveTab(tabs[newIndex] as 'stats' | 'generate' | 'search' | 'usage' | 'batch');
              }
            }}
            role="tab"
            aria-selected={activeTab === 'search'}
            aria-controls="search-panel"
            id="search-tab"
            tabIndex={activeTab === 'search' ? 0 : -1}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'search'
                ? 'border-ink-500 text-ink-700'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Search
          </button>
          <button
            onClick={() => setActiveTab('usage')}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const tabs = ['stats', 'generate', 'search', 'usage', 'batch'];
                const currentIndex = tabs.indexOf(activeTab);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                  newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                  newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                setActiveTab(tabs[newIndex] as 'stats' | 'generate' | 'search' | 'usage' | 'batch');
              }
            }}
            role="tab"
            aria-selected={activeTab === 'usage'}
            aria-controls="usage-panel"
            id="usage-tab"
            tabIndex={activeTab === 'usage' ? 0 : -1}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'usage'
                ? 'border-ink-500 text-ink-700'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Usage
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const tabs = ['stats', 'generate', 'search', 'usage', 'batch'];
                const currentIndex = tabs.indexOf(activeTab);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                  newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                  newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                setActiveTab(tabs[newIndex] as 'stats' | 'generate' | 'search' | 'usage' | 'batch');
              }
            }}
            role="tab"
            aria-selected={activeTab === 'batch'}
            aria-controls="batch-panel"
            id="batch-tab"
            tabIndex={activeTab === 'batch' ? 0 : -1}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'batch'
                ? 'border-ink-500 text-ink-700'
                : 'border-transparent text-ink-500 hover:text-ink-700 hover:border-ink-300'
            }`}
          >
            Batch
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'stats' && (
          <div role="tabpanel" id="stats-panel" aria-labelledby="stats-tab">
            {renderStatsTab()}
          </div>
        )}
        {activeTab === 'generate' && (
          <div role="tabpanel" id="generate-panel" aria-labelledby="generate-tab">
            {renderGenerateTab()}
          </div>
        )}
        {activeTab === 'search' && (
          <div role="tabpanel" id="search-panel" aria-labelledby="search-tab">
            {renderSearchTab()}
          </div>
        )}
        {activeTab === 'usage' && (
          <div role="tabpanel" id="usage-panel" aria-labelledby="usage-tab">
            {renderUsageTab()}
          </div>
        )}
        {activeTab === 'batch' && (
          <div role="tabpanel" id="batch-panel" aria-labelledby="batch-tab">
            {renderBatchTab()}
          </div>
        )}
      </div>
    </div>
  );
}