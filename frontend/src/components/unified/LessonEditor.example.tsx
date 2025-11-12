/**
 * Example usage of the LessonEditor component
 * This demonstrates how to integrate the component in different contexts
 */

import { useState } from 'react';
import LessonEditor from './LessonEditor';

// Example 1: Standalone usage (for DraftsModal)
export function StandaloneLessonEditor() {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState('# My Lesson\n\nStart writing your lesson content here...');

  const handleSave = async (newContent: string): Promise<void> => {
    // Simulate API call to save the lesson
    console.log('Saving lesson content:', newContent);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Update local state
    setContent(newContent);
    
    // Here you would typically make an API call to your backend
    // await fetch('/api/lessons', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ content: newContent })
    // });
  };

  const handleCancel = (): void => {
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <div className="p-8">
        <button
          onClick={() => setIsOpen(true)}
          className="px-6 py-3 bg-ink-600 text-white rounded-lg hover:bg-ink-700 transition-colors"
        >
          Open Lesson Editor
        </button>
        <div className="mt-4 p-4 bg-white rounded-lg border border-ink-200">
          <h3 className="font-semibold mb-2">Current Content:</h3>
          <pre className="text-sm text-ink-600 whitespace-pre-wrap">{content}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 p-4">
      <div className="w-full h-full max-w-6xl mx-auto">
        <LessonEditor
          content={content}
          onSave={handleSave}
          onCancel={handleCancel}
          autoSave={true}
        />
      </div>
    </div>
  );
}

// Example 2: Inline editing (for ChatMessage)
export function InlineLessonEditor() {
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(
    `# Music Lesson: Understanding Rhythm

## Learning Objectives
- Students will identify basic rhythm patterns
- Students will clap and count simple time signatures
- Students will create their own rhythm compositions

## Materials
- Whiteboard or smartboard
- rhythm sticks or hand clapping
- Simple percussion instruments (optional)

## Lesson Activities

### Warm-up (5 minutes)
Begin with a call-and-response clapping exercise.

### Main Activity (20 minutes)
1. Introduce quarter notes and eighth notes
2. Practice counting "1-and-2-and" patterns
3. Have students create 4-beat rhythm patterns

### Assessment (10 minutes)
Students perform their rhythm patterns for the class.

## Homework
Practice clapping the rhythm patterns learned in class.`
  );

  const handleSave = async (newContent: string): Promise<void> => {
    // Simulate saving to backend
    console.log('Saving inline lesson:', newContent);
    await new Promise(resolve => setTimeout(resolve, 800));
    setContent(newContent);
    setIsEditing(false);
  };

  const handleCancel = (): void => {
    setIsEditing(false);
  };

  const startEditing = (): void => {
    setIsEditing(true);
  };

  if (isEditing) {
    return (
      <div className="h-96 border border-ink-200 rounded-lg overflow-hidden">
        <LessonEditor
          content={content}
          onSave={handleSave}
          onCancel={handleCancel}
          autoSave={true}
        />
      </div>
    );
  }

  return (
    <div className="p-4 bg-parchment-50 rounded-lg border border-ink-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-ink-800">Music Lesson Plan</h3>
        <button
          onClick={startEditing}
          className="px-3 py-1.5 text-sm bg-ink-600 text-white rounded-md hover:bg-ink-700 transition-colors"
        >
          Edit Lesson
        </button>
      </div>
      <div className="prose prose-sm max-w-none">
        <pre className="whitespace-pre-wrap text-sm text-ink-700 font-mono">
          {content}
        </pre>
      </div>
    </div>
  );
}

// Example 3: Integration with existing draft system
export function DraftIntegrationExample() {
  const [currentDraft, setCurrentDraft] = useState({
    id: 'draft-123',
    title: 'Music Composition Basics',
    content: `# Music Composition Basics

## Overview
This lesson introduces students to the fundamentals of music composition.

## Key Concepts
- Melody
- Harmony  
- Rhythm
- Form

## Activities
1. Listen to example compositions
2. Analyze musical elements
3. Create simple melodies`,
  });

  const saveDraftToBackend = async (content: string): Promise<void> => {
    try {
      // Simulate API call to save draft
      const response = await fetch('/api/drafts', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: currentDraft.id,
          content,
          updatedAt: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save draft');
      }

      const updatedDraft = await response.json();
      setCurrentDraft(updatedDraft);
    } catch (error) {
      console.error('Error saving draft:', error);
      throw error;
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Draft: {currentDraft.title}</h2>
      <div className="h-96 border border-ink-200 rounded-lg overflow-hidden">
        <LessonEditor
          content={currentDraft.content}
          onSave={saveDraftToBackend}
          onCancel={() => console.log('Cancel editing')}
          autoSave={true}
        />
      </div>
    </div>
  );
}

// Default export for easy testing
export default function LessonEditorExamples() {
  const [activeExample, setActiveExample] = useState<'standalone' | 'inline' | 'draft'>('standalone');

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4 border-b border-ink-200 pb-4">
        <h1 className="text-2xl font-bold">Lesson Editor Examples</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveExample('standalone')}
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              activeExample === 'standalone'
                ? 'bg-ink-600 text-white'
                : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
            }`}
          >
            Standalone
          </button>
          <button
            onClick={() => setActiveExample('inline')}
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              activeExample === 'inline'
                ? 'bg-ink-600 text-white'
                : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
            }`}
          >
            Inline
          </button>
          <button
            onClick={() => setActiveExample('draft')}
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              activeExample === 'draft'
                ? 'bg-ink-600 text-white'
                : 'bg-parchment-200 text-ink-700 hover:bg-parchment-300'
            }`}
          >
            Draft Integration
          </button>
        </div>
      </div>

      {activeExample === 'standalone' && <StandaloneLessonEditor />}
      {activeExample === 'inline' && <InlineLessonEditor />}
      {activeExample === 'draft' && <DraftIntegrationExample />}
    </div>
  );
}