import React, { useState } from 'react';

interface MultiSelectObjectivesProps {
  selectedObjectives: string[];
  availableObjectives: string[];
  onSelectionChange: (selected: string[]) => void;
  label: string;
  placeholder?: string;
  selectedStandardsCount?: number; // Number of selected standards (for context)
}

export default function MultiSelectObjectives({
  selectedObjectives,
  availableObjectives,
  onSelectionChange,
  label,
  placeholder = "Select objectives...",
  selectedStandardsCount = 0
}: MultiSelectObjectivesProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter available objectives based on search term
  const filteredObjectives = availableObjectives.filter(objective =>
    objective.toLowerCase().includes(searchTerm.toLowerCase())
  );

  console.log('MultiSelectObjectives:', {
    selectedStandardsCount,
    availableObjectivesCount: availableObjectives.length,
    filteredObjectivesCount: filteredObjectives.length,
    selectedObjectivesCount: selectedObjectives.length,
    searchTerm
  });

  // Remove objective from selection
  const removeObjective = (objectiveToRemove: string) => {
    const newSelection = selectedObjectives.filter(o => o !== objectiveToRemove);
    onSelectionChange(newSelection);
  };

  // Add objective to selection
  const addObjective = (objectiveToAdd: string) => {
    if (!selectedObjectives.find(o => o === objectiveToAdd)) {
      const newSelection = [...selectedObjectives, objectiveToAdd];
      onSelectionChange(newSelection);
    }
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative">
      <label className="block text-xs font-semibold text-ink-700 mb-1 flex items-center justify-between">
        <span>{label}</span>
        {selectedStandardsCount > 0 && (
          <span className="text-xs font-normal text-ink-500">
            from {selectedStandardsCount} standard{selectedStandardsCount !== 1 ? 's' : ''}
          </span>
        )}
      </label>
      
      {/* Selected objectives display */}
      <div className="border border-ink-300 rounded-lg p-2 min-h-[60px] bg-parchment-50">
        {selectedObjectives.length === 0 ? (
          <div 
            className="text-ink-500 text-sm cursor-pointer hover:text-ink-700"
            onClick={() => setIsOpen(true)}
          >
            {placeholder}
          </div>
        ) : (
          <div className="space-y-1">
            {selectedObjectives.map(objective => {
              // Split objective into code and description (format: "K.CN.1.1 - Description")
              const parts = objective.split(' - ');
              const code = parts[0];
              const description = parts.slice(1).join(' - ');
              
              return (
                <div
                  key={objective}
                  className="flex items-center justify-between bg-ink-100 rounded px-2 py-1"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm text-ink-800">{code}</div>
                    {description && <div className="text-xs text-ink-600">{description}</div>}
                  </div>
                  <button
                    onClick={() => removeObjective(objective)}
                    className="ml-2 text-ink-500 hover:text-red-600 font-bold flex-shrink-0"
                    title="Remove"
                  >
                    ×
                  </button>
                </div>
              );
            })}
            {selectedObjectives.length > 0 && (
              <button
                onClick={() => setIsOpen(true)}
                className="text-ink-500 text-sm hover:text-ink-700 mt-1"
              >
                + Add more
              </button>
            )}
          </div>
        )}
      </div>

      {/* Dropdown for selection */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-ink-300 rounded-lg shadow-lg">
          <div className="p-2 border-b border-ink-200">
            <input
              type="text"
              placeholder="Search objectives..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-ink-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-ink-500"
              autoFocus
            />
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {filteredObjectives.length === 0 ? (
              <div className="p-3 text-ink-500 text-sm">
                {availableObjectives.length === 0 
                  ? (selectedStandardsCount === 0 
                      ? 'Select standards above to see their objectives'
                      : 'No objectives available for the selected standards')
                  : 'No objectives match your search'}
              </div>
            ) : (
              filteredObjectives.map(objective => {
                const isSelected = selectedObjectives.find(o => o === objective);
                // Split objective into code and description (format: "K.CN.1.1 - Description")
                const parts = objective.split(' - ');
                const code = parts[0];
                const description = parts.slice(1).join(' - ');
                
                return (
                  <div
                    key={objective}
                    onClick={() => !isSelected && addObjective(objective)}
                    className={`px-3 py-2 cursor-pointer border-b border-ink-100 last:border-b-0 ${
                      isSelected 
                        ? 'bg-ink-100 text-ink-500' 
                        : 'hover:bg-ink-50'
                    }`}
                  >
                    <div className="font-medium text-sm">{code}</div>
                    {description && <div className="text-xs text-ink-600 mt-0.5">{description}</div>}
                  </div>
                );
              })
            )}
          </div>
          
          <div className="p-2 border-t border-ink-200">
            <button
              onClick={() => {
                setIsOpen(false);
                setSearchTerm('');
              }}
              className="w-full px-3 py-1 bg-ink-200 text-ink-700 rounded text-sm hover:bg-ink-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => {
            setIsOpen(false);
            setSearchTerm('');
          }}
        />
      )}
    </div>
  );
}