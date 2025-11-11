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
    const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
      blue: { bg: 'bg-blue-50', text: 'text-blue-600', icon: 'text-blue-500' },
      green: { bg: 'bg-green-50', text: 'text-green-600', icon: 'text-green-500' },
      purple: { bg: 'bg-purple-50', text: 'text-purple-600', icon: 'text-purple-500' },
      yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600', icon: 'text-yellow-500' },
      indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600', icon: 'text-indigo-500' },
      pink: { bg: 'bg-pink-50', text: 'text-pink-600', icon: 'text-pink-500' },
      orange: { bg: 'bg-orange-50', text: 'text-orange-600', icon: 'text-orange-500' },
      teal: { bg: 'bg-teal-50', text: 'text-teal-600', icon: 'text-teal-500' },
      cyan: { bg: 'bg-cyan-50', text: 'text-cyan-600', icon: 'text-cyan-500' },
    };
    return colorMap[color] || colorMap.blue;
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading ingestion statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Ingestion Statistics</h2>
        <div className="flex items-center text-sm text-gray-500">
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
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className={`text-2xl font-bold ${colors.text}`}>{stat.value.toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
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
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View Detailed Reports →
          </button>
        </div>
      </div>
    </div>
  );
}