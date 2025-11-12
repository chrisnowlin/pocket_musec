import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { statsService, DatabaseStats } from '../services/statsService';

export interface IngestionStatusRef {
  refresh: () => Promise<void>;
}

const IngestionStatus = forwardRef<IngestionStatusRef>((props, ref) => {
  const [stats, setStats] = useState<DatabaseStats>({
    standards_count: 0,
    objectives_count: 0,
    sections_count: 0,
    strategies_count: 0,
    guidance_count: 0,
    relationships_count: 0,
    mappings_count: 0,
    glossary_count: 0,
    faq_count: 0,
    resource_count: 0,
    total_documents: 0,
    last_updated: '',
  });
  const [loading, setLoading] = useState(true);
  const [showDetailedReports, setShowDetailedReports] = useState(false);
  const [selectedContentType, setSelectedContentType] = useState<string | null>(null);
  const [contentItems, setContentItems] = useState<any[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const statsData = await statsService.getIngestionStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch ingestion stats:', error);
      // Keep default stats on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useImperativeHandle(ref, () => ({
    refresh: fetchStats,
  }));

  const statCards = [
    {
      title: 'Standards',
      value: stats.standards_count,
      icon: '📋',
      color: 'blue',
      description: 'NC Music Standards',
      contentType: 'standards'
    },
    {
      title: 'Objectives',
      value: stats.objectives_count,
      icon: '🎯',
      color: 'green',
      description: 'Learning Objectives',
      contentType: 'objectives'
    },
    {
      title: 'Teaching Strategies',
      value: stats.strategies_count,
      icon: '💡',
      color: 'purple',
      description: 'Pedagogical Strategies',
      contentType: 'strategies'
    },
    {
      title: 'Assessment Guidance',
      value: stats.guidance_count,
      icon: '📝',
      color: 'yellow',
      description: 'Assessment Examples',
      contentType: 'guidance'
    },
    {
      title: 'Alignment Relationships',
      value: stats.relationships_count,
      icon: '🔗',
      color: 'indigo',
      description: 'Standard Connections',
      contentType: 'relationships'
    },
    {
      title: 'Progression Mappings',
      value: stats.mappings_count,
      icon: '📈',
      color: 'pink',
      description: 'Grade Progressions',
      contentType: 'mappings'
    },
    {
      title: 'Glossary Terms',
      value: stats.glossary_count,
      icon: '📖',
      color: 'orange',
      description: 'Definitions',
      contentType: 'glossary'
    },
    {
      title: 'FAQ Entries',
      value: stats.faq_count,
      icon: '❓',
      color: 'teal',
      description: 'Common Questions',
      contentType: 'faq'
    },
    {
      title: 'Resource Links',
      value: stats.resource_count,
      icon: '🔧',
      color: 'cyan',
      description: 'External Resources',
      contentType: 'resources'
    },
  ];

  const handleContentTypeClick = async (contentType: string, title: string) => {
    setSelectedContentType(contentType);
    setLoadingItems(true);
    try {
      const items = await statsService.getContentItems(contentType, 500);
      setContentItems(items);
    } catch (error) {
      console.error(`Failed to fetch ${contentType} items:`, error);
      setContentItems([]);
    } finally {
      setLoadingItems(false);
    }
  };

  const renderContentItem = (item: any, contentType: string) => {
    switch (contentType) {
      case 'standards':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="font-semibold text-ink-800">{item.id}</p>
                <p className="text-sm text-ink-600 mt-1">{item.text}</p>
                <div className="flex gap-2 mt-2 text-xs text-ink-500">
                  <span>Grade: {item.grade_level}</span>
                  <span>•</span>
                  <span>{item.strand_code} - {item.strand_name}</span>
                </div>
              </div>
            </div>
          </div>
        );
      case 'objectives':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800 text-sm">{item.id}</p>
            <p className="text-sm text-ink-600 mt-1">{item.text}</p>
            <p className="text-xs text-ink-500 mt-1">Standard: {item.standard_id}</p>
          </div>
        );
      case 'strategies':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="text-sm text-ink-600">{item.text}</p>
            <div className="flex gap-2 mt-2 text-xs text-ink-500">
              <span>Grade: {item.grade_level}</span>
              {item.strand_code && <><span>•</span><span>Strand: {item.strand_code}</span></>}
            </div>
          </div>
        );
      case 'guidance':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="text-sm text-ink-600">{item.text}</p>
            <div className="flex gap-2 mt-2 text-xs text-ink-500">
              <span>Grade: {item.grade_level}</span>
              {item.strand_code && <><span>•</span><span>Strand: {item.strand_code}</span></>}
            </div>
          </div>
        );
      case 'relationships':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800 text-sm">{item.standard_id}</p>
            <p className="text-sm text-ink-600 mt-1">{item.description || 'No description'}</p>
            <div className="flex gap-2 mt-2 text-xs text-ink-500">
              <span>Type: {item.relationship_type}</span>
              <span>•</span>
              <span>Related: {item.related_standard_ids?.length || 0} standards</span>
            </div>
          </div>
        );
      case 'mappings':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800">{item.skill_name}</p>
            {item.progression_notes && (
              <p className="text-sm text-ink-600 mt-1">{item.progression_notes}</p>
            )}
            <div className="flex gap-2 mt-2 text-xs text-ink-500">
              <span>Grades: {item.grade_levels?.join(', ') || 'N/A'}</span>
            </div>
          </div>
        );
      case 'glossary':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800">{item.term}</p>
            <p className="text-sm text-ink-600 mt-1">{item.definition}</p>
          </div>
        );
      case 'faq':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800">{item.question}</p>
            <p className="text-sm text-ink-600 mt-1">{item.answer}</p>
            {item.category && (
              <p className="text-xs text-ink-500 mt-1">Category: {item.category}</p>
            )}
          </div>
        );
      case 'resources':
        return (
          <div key={item.id} className="p-3 bg-ink-50 rounded-lg mb-2">
            <p className="font-semibold text-ink-800">{item.resource_name}</p>
            {item.description && (
              <p className="text-sm text-ink-600 mt-1">{item.description}</p>
            )}
            {item.url && (
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-ink-500 hover:text-ink-700 mt-1 block">
                {item.url}
              </a>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  const getColorClasses = (color: string) => {
    // All cards use parchment theme with slight variations
    const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
      blue: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      green: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      purple: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      yellow: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      indigo: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      pink: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      orange: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      teal: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
      cyan: { bg: 'workspace-card', text: 'text-ink-700', icon: 'text-ink-600' },
    };
    return colorMap[color] || colorMap.blue;
  };

  if (loading) {
    return (
      <div className="workspace-card rounded-lg p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600 mx-auto mb-4"></div>
          <p className="text-ink-600">Loading ingestion statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace-card rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-ink-800">Ingestion Statistics</h2>
        <div className="flex items-center text-sm text-ink-600">
          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
          Last updated: {stats.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Never'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat, index) => {
          const colors = getColorClasses(stat.color);
          return (
            <div key={index} className={`${colors.bg} rounded-lg p-4`}>
              <div className="flex items-center">
                <div className={`text-2xl mr-3 ${colors.icon}`}>{stat.icon}</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-ink-600">{stat.title}</p>
                  <p className={`text-2xl font-bold ${colors.text}`}>{stat.value.toLocaleString()}</p>
                  <p className="text-xs text-ink-500 mt-1">{stat.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-ink-300">
        <div className="flex items-center justify-between">
          <div className="text-sm text-ink-600">
            <strong>Total Content Items:</strong> {(
              stats.standards_count + 
              stats.objectives_count + 
              stats.sections_count + 
              stats.strategies_count + 
              stats.guidance_count + 
              stats.relationships_count + 
              stats.mappings_count + 
              stats.glossary_count + 
              stats.faq_count + 
              stats.resource_count
            ).toLocaleString()}
          </div>
          <button 
            onClick={() => setShowDetailedReports(true)}
            className="text-sm text-ink-600 hover:text-ink-800 font-medium transition-colors cursor-pointer"
          >
            View Detailed Reports →
          </button>
        </div>
      </div>

      {showDetailedReports && (
        <div
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4"
          onClick={() => setShowDetailedReports(false)}
        >
          <div
            className="workspace-card rounded-2xl max-w-3xl w-full max-h-[80vh] p-6 shadow-xl space-y-4 flex flex-col"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-ink-800">Detailed Ingestion Reports</h3>
              <button 
                onClick={() => setShowDetailedReports(false)} 
                className="text-ink-500 hover:text-ink-700 text-2xl leading-none w-8 h-8 flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-semibold text-ink-700 mb-3 uppercase tracking-wide">
                    Content Statistics
                  </h4>
                  <div className="space-y-2">
                    {statCards.map((stat, index) => {
                      const colors = getColorClasses(stat.color);
                      const total = stats.standards_count + 
                           stats.objectives_count + 
                           stats.sections_count + 
                           stats.strategies_count + 
                           stats.guidance_count + 
                           stats.relationships_count + 
                           stats.mappings_count + 
                           stats.glossary_count + 
                           stats.faq_count + 
                           stats.resource_count;
                      const percentage = total > 0 
                        ? ((stat.value / total) * 100).toFixed(1)
                        : '0.0';
                      
                      return (
                        <div 
                          key={index} 
                          onClick={() => stat.value > 0 && handleContentTypeClick(stat.contentType, stat.title)}
                          className={`flex items-center justify-between p-3 bg-ink-50 rounded-lg transition-colors ${
                            stat.value > 0 ? 'cursor-pointer hover:bg-ink-100' : 'opacity-50'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-xl">{stat.icon}</span>
                            <div>
                              <p className="text-sm font-medium text-ink-700">{stat.title}</p>
                              <p className="text-xs text-ink-500">{stat.description}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-ink-800">{stat.value.toLocaleString()}</p>
                            <p className="text-xs text-ink-500">{percentage}%</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-4 border-t border-ink-300">
                  <h4 className="text-sm font-semibold text-ink-700 mb-3 uppercase tracking-wide">
                    Summary
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-ink-50 rounded-lg">
                      <p className="text-xs text-ink-500 mb-1">Total Content Items</p>
                      <p className="text-2xl font-bold text-ink-800">
                        {(
                          stats.standards_count + 
                          stats.objectives_count + 
                          stats.sections_count + 
                          stats.strategies_count + 
                          stats.guidance_count + 
                          stats.relationships_count + 
                          stats.mappings_count + 
                          stats.glossary_count + 
                          stats.faq_count + 
                          stats.resource_count
                        ).toLocaleString()}
                      </p>
                    </div>
                    <div className="p-4 bg-ink-50 rounded-lg">
                      <p className="text-xs text-ink-500 mb-1">Last Updated</p>
                      <p className="text-sm font-semibold text-ink-800">
                        {stats.last_updated 
                          ? new Date(stats.last_updated).toLocaleString() 
                          : 'Never'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-ink-300">
              <button
                onClick={() => {
                  setShowDetailedReports(false);
                  setSelectedContentType(null);
                  setContentItems([]);
                }}
                className="px-4 py-2 bg-ink-600 text-white rounded-lg hover:bg-ink-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedContentType && (
        <div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-4"
          onClick={() => {
            setSelectedContentType(null);
            setContentItems([]);
          }}
        >
          <div
            className="workspace-card rounded-2xl max-w-4xl w-full max-h-[85vh] p-6 shadow-xl space-y-4 flex flex-col"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-ink-800">
                {statCards.find(card => card.contentType === selectedContentType)?.title || 'Content Items'}
              </h3>
              <button 
                onClick={() => {
                  setSelectedContentType(null);
                  setContentItems([]);
                }} 
                className="text-ink-500 hover:text-ink-700 text-2xl leading-none w-8 h-8 flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loadingItems ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ink-600 mx-auto mb-4"></div>
                  <p className="text-ink-600">Loading items...</p>
                </div>
              ) : contentItems.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-ink-600">No items found</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-ink-500 mb-4">
                    Showing {contentItems.length} item{contentItems.length !== 1 ? 's' : ''}
                  </p>
                  {contentItems.map((item) => renderContentItem(item, selectedContentType))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t border-ink-300">
              <button
                onClick={() => {
                  setSelectedContentType(null);
                  setContentItems([]);
                }}
                className="px-4 py-2 bg-ink-600 text-white rounded-lg hover:bg-ink-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

IngestionStatus.displayName = 'IngestionStatus';

export default IngestionStatus;