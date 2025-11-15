import React, { useState } from 'react';
import type { StandardRecord } from '../../lib/types';

interface MultiSelectStandardProps {
  standards: StandardRecord[];
  selectedStandards: StandardRecord[];
  availableStandards: StandardRecord[];
  onSelectionChange: (selected: StandardRecord[]) => void;
  label: string;
  placeholder?: string;
}

export default function MultiSelectStandard({
  standards,
  selectedStandards,
  availableStandards,
  onSelectionChange,
  label,
  placeholder = "Select standards..."
}: MultiSelectStandardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter available standards based on search term
  const filteredStandards = availableStandards.filter(standard =>
    standard.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    standard.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  console.log('MultiSelectStandard:', {
    availableStandardsCount: availableStandards.length,
    filteredStandardsCount: filteredStandards.length,
    searchTerm,
    firstAvailable: availableStandards[0]?.code,
    firstFiltered: filteredStandards[0]?.code
  });

  // Remove standard from selection
  const removeStandard = (standardToRemove: StandardRecord) => {
    const newSelection = selectedStandards.filter(s => s.id !== standardToRemove.id);
    onSelectionChange(newSelection);
  };

  // Add standard to selection
  const addStandard = (standardToAdd: StandardRecord) => {
    if (!selectedStandards.find(s => s.id === standardToAdd.id)) {
      const newSelection = [...selectedStandards, standardToAdd];
      onSelectionChange(newSelection);
    }
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative">
      <label className="block text-xs font-semibold text-ink-700 mb-1">
        {label}
      </label>
      
      {/* Selected standards display */}
      <div className="border border-ink-300 rounded-lg p-2 min-h-[60px] bg-parchment-50">
        {selectedStandards.length === 0 ? (
          <div 
            className="text-ink-500 text-sm cursor-pointer hover:text-ink-700"
            onClick={() => setIsOpen(true)}
          >
            {placeholder}
          </div>
        ) : (
          <div className="space-y-1">
            {selectedStandards.map(standard => (
              <div
                key={standard.id}
                className="flex items-center justify-between bg-ink-100 rounded px-2 py-1 text-sm"
              >
                <div className="flex-1">
                  <span className="font-medium text-ink-800">{standard.code}</span>
                  <span className="text-ink-600 ml-2">{standard.description}</span>
                </div>
                <button
                  onClick={() => removeStandard(standard)}
                  className="ml-2 text-ink-500 hover:text-red-600 font-bold"
                  title="Remove"
                >
                  ×
                </button>
              </div>
            ))}
            {selectedStandards.length > 0 && (
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
              placeholder="Search standards..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-ink-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-ink-500"
              autoFocus
            />
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {filteredStandards.length === 0 ? (
              <div className="p-3 text-ink-500 text-sm">
                {availableStandards.length === 0 
                  ? 'No standards available for the selected grade and strand'
                  : 'No standards match your search'}
              </div>
            ) : (
              filteredStandards.map(standard => {
                const isSelected = selectedStandards.find(s => s.id === standard.id);
                return (
                  <div
                    key={standard.id}
                    onClick={() => !isSelected && addStandard(standard)}
                    className={`px-3 py-2 cursor-pointer border-b border-ink-100 last:border-b-0 ${
                      isSelected 
                        ? 'bg-ink-100 text-ink-500' 
                        : 'hover:bg-ink-50'
                    }`}
                  >
                    <div className="font-medium text-sm">{standard.code}</div>
                    <div className="text-xs text-ink-600">{standard.description}</div>
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