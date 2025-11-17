import { useMemo } from 'react';
import type { StandardRecord } from '../../lib/types';
import { gradeOptions, strandOptions } from '../../constants/unified';
import { frontendToBackendGrade, frontendToBackendStrand } from '../../lib/gradeUtils';

interface BrowsePanelProps {
  standards: StandardRecord[];
  selectedGrade: string;
  selectedStrand: string;
  selectedStandard: StandardRecord | null;
  browseQuery: string;
  onGradeChange: (grade: string) => void;
  onStrandChange: (strand: string) => void;
  onStandardSelect: (standard: StandardRecord) => void;
  onBrowseQueryChange: (query: string) => void;
  onStartChat: (standard: StandardRecord, prompt: string) => void;
}

export default function BrowsePanel({
  standards,
  selectedGrade,
  selectedStrand,
  selectedStandard,
  browseQuery,
  onGradeChange,
  onStrandChange,
  onStandardSelect,
  onBrowseQueryChange,
  onStartChat,
}: BrowsePanelProps) {
  const filteredStandards = useMemo(() => {
    return standards.filter((standard) => {
      // Handle "All Grades" and "All Strands" selections
      // Note: standard.grade is already in frontend format (e.g., "Kindergarten", "Grade 3")
      // from the API response, so we compare directly with selectedGrade
      // Use case-insensitive comparison to handle any formatting inconsistencies
      const matchesGrade = selectedGrade === 'All Grades' || !selectedGrade
        ? true
        : standard.grade?.trim().toLowerCase() === selectedGrade.trim().toLowerCase();
      
      const matchesStrand = selectedStrand === 'All Strands' || !selectedStrand
        ? true
        : standard.strandCode === frontendToBackendStrand(selectedStrand);
      
      const matchesSearch = browseQuery
        ? standard.title.toLowerCase().includes(browseQuery.toLowerCase()) ||
          standard.description.toLowerCase().includes(browseQuery.toLowerCase()) ||
          standard.code.toLowerCase().includes(browseQuery.toLowerCase())
        : true;
      return matchesGrade && matchesStrand && matchesSearch;
    });
  }, [browseQuery, selectedGrade, selectedStrand, standards]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 pb-4">
        <div className="workspace-card p-4 space-y-3">
          <div className="flex items-center gap-4 mb-3">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search standards, objectives, or topics..."
                value={browseQuery}
                onChange={(event) => onBrowseQueryChange(event.target.value)}
                className="w-full border border-ink-300 rounded-lg px-4 py-2 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 focus:border-transparent bg-parchment-50 text-ink-800"
              />
              <svg
                className="w-5 h-5 text-ink-500 absolute left-3 top-2.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
          <div className="flex flex-col gap-3 items-center">
            <div className="flex gap-2 flex-wrap justify-center">
              <button
                onClick={() => onGradeChange('All Grades')}
                className={`px-3 py-1 text-xs font-medium rounded-full border ${
                  selectedGrade === 'All Grades' || !selectedGrade
                    ? 'bg-parchment-200 text-ink-700 border-ink-300'
                    : 'bg-parchment-100 text-ink-600 border-ink-300 hover:bg-parchment-200'
                }`}
              >
                All Grades
              </button>
              {gradeOptions.slice(0, 6).map((grade) => (
                <button
                  key={grade}
                  onClick={() => onGradeChange(grade)}
                  className={`px-3 py-1 text-xs font-medium rounded-full border ${
                    selectedGrade === grade
                      ? 'bg-parchment-200 text-ink-700 border-ink-300'
                      : 'bg-parchment-100 text-ink-600 border-ink-300 hover:bg-parchment-200'
                  }`}
                >
                  {grade}
                </button>
              ))}
            </div>
            <div className="flex gap-2 flex-wrap justify-center">
              <button
                onClick={() => onStrandChange('All Strands')}
                className={`px-3 py-1 text-xs font-medium rounded-full border ${
                  selectedStrand === 'All Strands' || !selectedStrand
                    ? 'bg-parchment-200 text-ink-700 border-ink-300'
                    : 'bg-parchment-100 text-ink-600 border-ink-300 hover:bg-parchment-200'
                }`}
              >
                All Strands
              </button>
              {strandOptions.map((strand) => (
                <button
                  key={strand}
                  onClick={() => onStrandChange(strand)}
                  className={`px-3 py-1 text-xs font-medium rounded-full border ${
                    selectedStrand === strand
                      ? 'bg-parchment-200 text-ink-700 border-ink-300'
                      : 'bg-parchment-100 text-ink-600 border-ink-300 hover:bg-parchment-200'
                  }`}
                >
                  {strand}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 scrollable px-6 pb-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-ink-800">
              Standards for {selectedGrade === 'All Grades' || !selectedGrade ? 'All Grades' : selectedGrade} · {selectedStrand === 'All Strands' || !selectedStrand ? 'All Strands' : selectedStrand}
            </h2>
            <span className="text-sm text-ink-600">{filteredStandards.length} standards found</span>
          </div>
          <div className="space-y-3">
            {filteredStandards.map((standard) => (
              <div
                key={standard.id}
                className={`border ${
                  selectedStandard?.id === standard.id
                    ? 'border-ink-400 bg-parchment-200'
                    : 'border-ink-300 bg-parchment-50'
                } rounded-lg p-4 hover:bg-parchment-100 cursor-pointer transition-colors`}
                onClick={() => onStandardSelect(standard)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono font-semibold text-ink-700 bg-parchment-200 px-2 py-1 rounded">
                        {standard.code}
                      </span>
                      <span className="text-xs text-ink-600">{standard.strandName} Strand</span>
                    </div>
                    <h3 className="font-medium text-ink-800 mb-2">{standard.title}</h3>
                    <div className="flex items-center gap-4 text-sm text-ink-600">
                      <span className="flex items-center gap-1">
                        <svg
                          className="w-4 h-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                          />
                        </svg>
                        {standard.objectives} objectives
                      </span>
                      <span className="flex items-center gap-1">
                        <svg
                          className="w-4 h-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {standard.lastUsed ?? 'Recently used'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const prompt = `Start crafting a lesson centered on ${standard.code} - ${standard.title}`;
                      onStartChat(standard, prompt);
                    }}
                    className={`text-sm font-medium ml-4 whitespace-nowrap ${
                      selectedStandard?.id === standard.id
                        ? 'text-ink-700 hover:text-ink-800'
                        : 'text-ink-600 hover:text-ink-700'
                    }`}
                  >
                    Start Chat →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
