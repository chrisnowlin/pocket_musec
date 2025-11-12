import { useState } from 'react';

interface TemplateCreationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveTemplate: (name: string, description: string) => void;
}

export default function TemplateCreationModal({
  isOpen,
  onClose,
  onSaveTemplate,
}: TemplateCreationModalProps) {
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');

  if (!isOpen) return null;

  const handleSave = () => {
    if (templateName.trim() && templateDescription.trim()) {
      onSaveTemplate(templateName.trim(), templateDescription.trim());
      setTemplateName('');
      setTemplateDescription('');
    }
  };

  const handleCancel = () => {
    setTemplateName('');
    setTemplateDescription('');
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={handleCancel}
    >
      <div
        className="workspace-card rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-800">Save as Template</h3>
          <button onClick={handleCancel} className="text-ink-500 hover:text-ink-700">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1">
              Template Name *
            </label>
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="e.g., Third Grade Rhythm Lesson"
              className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-700 mb-1">
              Description *
            </label>
            <textarea
              value={templateDescription}
              onChange={(e) => setTemplateDescription(e.target.value)}
              placeholder="Describe what this lesson template covers..."
              rows={3}
              className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-ink-200">
          <button
            onClick={handleCancel}
            className="px-4 py-2 bg-parchment-200 text-ink-700 rounded-md hover:bg-parchment-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!templateName.trim() || !templateDescription.trim()}
            className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700 transition-colors disabled:bg-ink-400 disabled:cursor-not-allowed"
          >
            Save Template
          </button>
        </div>
      </div>
    </div>
  );
}