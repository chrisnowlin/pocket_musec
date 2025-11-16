import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DraftPreview from '../DraftPreview';
import type { DraftItem } from '../../../types/unified';
import type { LessonDocumentM2 } from '../../../lib/types';

function createM2LessonDocument(overrides: Partial<LessonDocumentM2> = {}): LessonDocumentM2 {
  return {
    id: 'doc-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    version: 'm2.0',
    title: 'Sample Lesson',
    grade: 'Grade 3',
    strands: ['Rhythm'],
    standards: [],
    objectives: [],
    content: {
      materials: [],
      warmup: '',
      activities: [],
      assessment: '',
      differentiation: '',
      exit_ticket: '',
      notes: 'Structured notes content',
      prerequisites: '',
      accommodations: '',
      homework: '',
      reflection: '',
      timing: { total_minutes: 45 },
    },
    citations: [],
    revision: 1,
    ...overrides,
  };
}

describe('DraftPreview', () => {
  it('renders m2.0 lesson_document notes when present', () => {
    const draft: DraftItem = {
      id: 'draft-1',
      title: 'M2 Draft',
      content: 'Legacy content that should be ignored when lesson_document is present',
      metadata: {
        lesson_document: createM2LessonDocument({
          content: {
            materials: [],
            warmup: '',
            activities: [],
            assessment: '',
            differentiation: '',
            exit_ticket: '',
            notes: 'Structured notes content',
            prerequisites: '',
            accommodations: '',
            homework: '',
            reflection: '',
            timing: { total_minutes: 45 },
          },
        }),
      },
      grade: 'Grade 3',
      strand: 'Rhythm',
      standard: undefined,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-02T00:00:00Z',
      originalContent: undefined,
    };

    render(<DraftPreview draft={draft} />);

    // Prefer structured notes content over legacy content
    expect(screen.getByText('Structured notes content')).toBeInTheDocument();
    expect(
      screen.queryByText('Legacy content that should be ignored when lesson_document is present'),
    ).not.toBeInTheDocument();
  });
});

