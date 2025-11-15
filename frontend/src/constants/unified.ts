import type { ConversationGroup, QuickAccessLink, QuickStats } from '../types/unified';
import type { StandardRecord } from '../lib/types';

export const gradeOptions = [
  'All Grades',
  'Kindergarten',
  'Grade 1',
  'Grade 2',
  'Grade 3',
  'Grade 4',
  'Grade 5',
  'Grade 6',
  'Grade 7',
  'Grade 8',
  // Proficiency levels for high school
  'Novice',
  'Developing',
  'Intermediate',
  'Accomplished',
  'Advanced',
];

export const strandOptions = ['All Strands', 'Connect', 'Create', 'Respond', 'Present'];

export const standardLibrary: StandardRecord[] = [];

export const conversationGroups: ConversationGroup[] = [
  {
    label: 'Today',
    items: [
      { id: 'sample-1', title: 'Grade 3 · Create Strand', hint: '2 hours ago · 12 messages', active: true },
      { id: 'sample-2', title: 'Grade 5 Rhythm Focus', hint: '4 hours ago · 8 messages', active: false },
    ],
  },
  {
    label: 'This Week',
    items: [
      { id: 'sample-3', title: 'Grade 1 · Present Singing', hint: '2 days ago · 15 messages', active: false },
      { id: 'sample-4', title: 'Kindergarten Movement', hint: '3 days ago · 6 messages', active: false },
    ],
  },
];

export const quickAccessLinks: QuickAccessLink[] = [];

export const quickStats: QuickStats = {
  lessonsCreated: 23,
  activeDrafts: 8,
};

// File Storage Constants
export const FILE_STORAGE_CONSTANTS = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB in bytes
  ALLOWED_EXTENSIONS: ['.pdf', '.txt', '.doc', '.docx'],
  SUPPORTED_MIME_TYPES: [
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ],
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
};

// File Storage Messages
export const FILE_STORAGE_MESSAGES = {
  DUPLICATE_FILE: 'This file has already been uploaded and processed.',
  FILE_TOO_LARGE: 'File size exceeds the maximum allowed size of 10MB.',
  INVALID_FILE_TYPE: 'File type not supported. Please upload a PDF, TXT, or DOC file.',
  UPLOAD_SUCCESS: 'File uploaded successfully.',
  UPLOAD_FAILED: 'File upload failed. Please try again.',
  DOWNLOAD_FAILED: 'File download failed. Please try again.',
  PROCESSING_STARTED: 'File processing has started. You will be notified when it completes.',
  PROCESSING_FAILED: 'File processing failed. Please check the file and try again.',
};
