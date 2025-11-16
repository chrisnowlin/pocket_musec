import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DraftsModal from '../DraftsModal';
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
      notes: 'Original structured notes',
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

describe('DraftsModal', () => {
  it('updates m2.0 lesson_document notes when saving via LessonEditor', async () => {
    const user = userEvent.setup();

    const lessonDocument = createM2LessonDocument();

    const draft: DraftItem = {
      id: 'draft-1',
      title: 'M2 Draft',
      content: 'Legacy content',
      metadata: {
        lesson_document: lessonDocument,
      },
      grade: 'Grade 3',
      strand: 'Rhythm',
      standard: undefined,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-02T00:00:00Z',
      originalContent: undefined,
    };

    const onUpdateDraft = vi.fn().mockResolvedValue({
      ...draft,
      content: 'Updated markdown',
      metadata: {
        lesson_document: {
          ...lessonDocument,
          content: {
            ...lessonDocument.content,
            notes: 'Updated markdown',
          },
          revision: lessonDocument.revision + 1,
        },
      },
      updatedAt: '2024-01-03T00:00:00Z',
    } as DraftItem);

    render(
      <DraftsModal
        isOpen={true}
        onClose={() => {}}
        drafts={[draft]}
        isLoading={false}
        onOpenDraft={vi.fn()}
        onDeleteDraft={vi.fn()}
        onUpdateDraft={onUpdateDraft}
      />,
    );

    // Open the editor for the draft
    await user.click(screen.getByRole('button', { name: /Edit draft:/i }));

    // LessonEditor should show legacy content initially
    const textarea = await screen.findByDisplayValue('Legacy content');

    await user.clear(textarea);
    await user.type(textarea, 'Updated markdown');

    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(onUpdateDraft).toHaveBeenCalledTimes(1);
    });

    const [, payload] = onUpdateDraft.mock.calls[0];

    expect(payload).toMatchObject({
      content: 'Updated markdown',
      title: 'M2 Draft',
      metadata: {
        lesson_document: {
          content: {
            notes: 'Updated markdown',
          },
        },
      },
    });
  });
});

