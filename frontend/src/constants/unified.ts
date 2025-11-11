import type { ConversationGroup, QuickAccessLink, QuickStats } from '../types/unified';
import type { StandardRecord } from '../lib/types';

export const gradeOptions = [
  'Kindergarten',
  'Grade 1',
  'Grade 2',
  'Grade 3',
  'Grade 4',
  'Grade 5',
  'Grade 6',
  'Grade 7',
  'Grade 8',
];

export const strandOptions = ['Connect', 'Create', 'Respond', 'Present'];

export const standardLibrary: StandardRecord[] = [
  {
    id: 'cn-3-1',
    code: '3.CN.1',
    strand_code: 'CN',
    strand_name: 'Connect',
    grade: 'Grade 3',
    title: 'Understand relationships between music, other disciplines, and daily life',
    description:
      'Students explore how music relates to other subjects, cultures, and real‑world experiences.',
    objectives: 4,
    last_used: '2 days ago',
    learningObjectives: [
      'Explain how music connects to storytelling and visual arts.',
      'Describe the influence of music on community events.',
      'Compare how music reflects societal celebrations.',
    ],
  },
  {
    id: 'cn-3-2',
    code: '3.CN.2',
    strand_code: 'CN',
    strand_name: 'Connect',
    grade: 'Grade 3',
    title: 'Explore interdisciplinary and global music connections',
    description:
      'Students discover musical ideas across cultures and link them to science, history, and language.',
    objectives: 3,
    last_used: 'Never used',
    learningObjectives: [
      'Identify musical patterns shared across cultures.',
      'Relate rhythms to mathematical fractions.',
      'Discuss how music preserves historical stories.',
    ],
  },
  {
    id: 'cr-4-1',
    code: '4.CR.1',
    strand_code: 'CR',
    strand_name: 'Create',
    grade: 'Grade 4',
    title: 'Create short compositions using classroom instruments',
    description:
      'Students improvise and notate ideas that incorporate steady beat and contrasting dynamics.',
    objectives: 5,
    last_used: '1 week ago',
    learningObjectives: [
      'Write rhythm patterns with quarter and eighth notes.',
      'Layer dynamics to create contrast.',
      'Perform composition with peers.',
    ],
  },
];

export const conversationGroups: ConversationGroup[] = [
  {
    label: 'Today',
    items: [
      { title: 'Grade 3 · Create Strand', hint: '2 hours ago · 12 messages', active: true },
      { title: 'Grade 5 Rhythm Focus', hint: '4 hours ago · 8 messages', active: false },
    ],
  },
  {
    label: 'This Week',
    items: [
      { title: 'Grade 1 · Present Singing', hint: '2 days ago · 15 messages', active: false },
      { title: 'Kindergarten Movement', hint: '3 days ago · 6 messages', active: false },
    ],
  },
];

export const quickAccessLinks: QuickAccessLink[] = [
  { label: 'Templates', hint: 'Saved song maps' },
  { label: 'Saved Drafts', hint: '8 drafts' },
];

export const quickStats: QuickStats = {
  lessonsCreated: 23,
  activeDrafts: 8,
};
