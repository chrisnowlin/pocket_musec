import { useState, useEffect } from 'react';
import { statsService, DatabaseStats } from '../services/statsService';

export default function IngestionStatus() {
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

  useEffect(() => {
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

    fetchStats();
  }, []);

  const statCards = [
    {
      title: 'Standards',
      value: stats.standards_count,
      icon: '📋',
      color: 'blue',
      description: 'NC Music Standards'
    },
    {
      title: 'Objectives',
      value: stats.objectives_count,
      icon: '🎯',
      color: 'green',
      description: 'Learning Objectives'
    },
    {
      title: 'Teaching Strategies',
      value: stats.strategies_count,
      icon: '💡',
      color: 'purple',
      description: 'Pedagogical Strategies'
    },
    {
      title: 'Assessment Guidance',
      value: stats.guidance_count,
      icon: '📝',
      color: 'yellow',
      description: 'Assessment Examples'
    },
    {
      title: 'Alignment Relationships',
      value: stats.relationships_count,
      icon: '🔗',
      color: 'indigo',
      description: 'Standard Connections'
    },
    {
      title: 'Progression Mappings',
      value: stats.mappings_count,
      icon: '📈',
      color: 'pink',
      description: 'Grade Progressions'
    },
    {
      title: 'Glossary Terms',
      value: stats.glossary_count,
      icon: '📖',
      color: 'orange',
      description: 'Definitions'
    },
    {
      title: 'FAQ Entries',
      value: stats.faq_count,
      icon: '❓',
      color: 'teal',
      description: 'Common Questions'
    },
    {
      title: 'Resource Links',
      value: stats.resource_count,
      icon: '🔧',
      color: 'cyan',
      description: 'External Resources'
    },
  ];

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
          <button className="text-sm text-ink-600 hover:text-ink-800 font-medium">
            View Detailed Reports →
          </button>
        </div>
      </div>
    </div>
  );
}