import React from 'react';
import { Link } from 'react-router-dom';

const PresentationNavigation: React.FC = () => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-blue-900 mb-1">Presentation System</h3>
          <p className="text-sm text-blue-700">
            Create, manage, and view presentations from your lesson content
          </p>
        </div>
        <Link
          to="/presentations"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors"
        >
          Open Presentation Manager
        </Link>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-blue-800">Generate presentations from lessons</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-blue-800">Multiple export formats (PPTX, PDF, JSON)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-blue-800">Real-time job progress tracking</span>
        </div>
      </div>
    </div>
  );
};

export default PresentationNavigation;