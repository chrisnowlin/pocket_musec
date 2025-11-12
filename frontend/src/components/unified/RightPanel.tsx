import type { StandardRecord, SessionResponsePayload } from '../../lib/types';
import type { ViewMode, StorageInfo } from '../../types/unified';
import { gradeOptions, strandOptions } from '../../constants/unified';

interface RightPanelProps {
  width: number;
  selectedGrade: string;
  selectedStrand: string;
  selectedStandard: StandardRecord | null;
  selectedObjective: string | null;
  lessonContext: string;
  lessonDuration: string;
  classSize: string;
  standards: StandardRecord[];
  session: SessionResponsePayload | null;
  sessionError: string | null;
  mode: ViewMode;
  messageCount: number;
  storageInfo: StorageInfo | null;
  draftCount: number;
  lessonsCount: number;
  isRetryingSession?: boolean;
  retrySuccess?: boolean | null;
  retryMessage?: string;
  onGradeChange: (grade: string) => void;
  onStrandChange: (strand: string) => void;
  onStandardChange: (standard: StandardRecord | null) => void;
  onObjectiveChange: (objective: string | null) => void;
  onLessonContextChange: (context: string) => void;
  onLessonDurationChange: (duration: string) => void;
  onClassSizeChange: (size: string) => void;
  onBrowseStandards: () => void;
  onViewConversations?: () => void;
  onViewMessages?: () => void;
  onViewDrafts?: () => void;
  onRetrySession?: () => Promise<SessionResponsePayload | null>;
}

export default function RightPanel({
  width,
  selectedGrade,
  selectedStrand,
  selectedStandard,
  selectedObjective,
  lessonContext,
  lessonDuration,
  classSize,
  standards,
  session,
  sessionError,
  mode,
  messageCount,
  storageInfo,
  draftCount,
  lessonsCount,
  isRetryingSession = false,
  retrySuccess = null,
  retryMessage = '',
  onGradeChange,
  onStrandChange,
  onStandardChange,
  onObjectiveChange,
  onLessonContextChange,
  onLessonDurationChange,
  onClassSizeChange,
  onBrowseStandards,
  onViewConversations,
  onViewMessages,
  onViewDrafts,
  onRetrySession,
}: RightPanelProps) {
  const sessionStatusLabel = session
    ? 'Connected to PocketMusec'
    : sessionError
    ? 'Session not responding'
    : 'Waking up the AI';
  const sessionStatusTone = session
    ? 'bg-parchment-200 text-ink-700 border-ink-300'
    : sessionError
    ? 'bg-parchment-300 text-ink-800 border-ink-400'
    : 'bg-parchment-200 text-ink-700 border-ink-300';
  const sessionStatusDetail = session ? 'Live' : sessionError ? 'Retry' : 'Loading';

  return (
    <aside
      id="rightPanel"
      className="border-l border-ink-300 flex flex-col panel workspace-panel-glass"
      style={{ width: `${width}px`, minWidth: '300px', maxWidth: '600px' }}
    >
      <div className="border-b border-ink-300 bg-parchment-50 px-6 py-4">
        <h2 className="font-semibold text-ink-800">Context & Configuration</h2>
        <p className="text-xs text-ink-600 mt-1">Lesson settings, processing options, and assets</p>
      </div>

      <div className="flex-1 scrollable p-6 space-y-4">
        <div className="workspace-card p-4 space-y-4">
          {/* Current Selections */}
          <div>
            <h3 className="font-semibold text-ink-800 mb-3 flex items-center gap-2">
              <svg
                className="w-5 h-5 text-ink-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Current Selections
            </h3>
            <div className="space-y-3 text-sm text-ink-700">
              <div>
                <label className="block text-xs font-semibold text-ink-700 mb-1">
                  Grade Level
                </label>
                <select
                  value={selectedGrade}
                  onChange={(event) => {
                    onGradeChange(event.target.value);
                    onObjectiveChange(null);
                  }}
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
                >
                  {gradeOptions.map((grade) => (
                    <option key={grade} value={grade}>
                      {grade}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-ink-700 mb-1">Strand</label>
                <select
                  value={selectedStrand}
                  onChange={(event) => {
                    onStrandChange(event.target.value);
                    onObjectiveChange(null);
                  }}
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
                >
                  {strandOptions.map((strand) => (
                    <option key={strand} value={strand}>
                      {strand}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-ink-700 mb-1">Standard</label>
                <select
                  value={selectedStandard?.id || ''}
                  onChange={(event) => {
                    const standard = standards.find((s) => s.id === event.target.value);
                    onStandardChange(standard || null);
                    onObjectiveChange(null);
                  }}
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
                >
                  <option value="">Not selected yet</option>
                  {standards
                    .filter(
                      (standard) =>
                        standard.grade === selectedGrade && standard.strand_name === selectedStrand
                    )
                    .map((standard) => (
                      <option key={standard.id} value={standard.id}>
                        {standard.code} - {standard.title}
                      </option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-ink-700 mb-1">Objective</label>
                <select
                  value={selectedObjective || ''}
                  onChange={(event) => onObjectiveChange(event.target.value || null)}
                  disabled={
                    !selectedStandard ||
                    !selectedStandard.learningObjectives ||
                    selectedStandard.learningObjectives.length === 0
                  }
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 disabled:bg-parchment-200 disabled:text-ink-500 disabled:cursor-not-allowed bg-parchment-50 text-ink-800"
                >
                  <option value="">
                    {!selectedStandard
                      ? 'Select a standard first'
                      : !selectedStandard.learningObjectives ||
                        selectedStandard.learningObjectives.length === 0
                      ? 'No objectives available'
                      : 'Not selected yet'}
                  </option>
                  {selectedStandard?.learningObjectives?.map((objective, index) => (
                    <option key={index} value={objective}>
                      {objective}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button
              onClick={onBrowseStandards}
              className="mt-4 w-full px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
            >
              Browse Standards
            </button>
          </div>

          {/* Lesson Settings */}
          <div className="border-t border-ink-300 pt-4">
            <h3 className="font-semibold text-ink-800">Lesson Settings</h3>
            <div>
              <label className="text-xs font-semibold text-ink-700 mb-1 block">
                Additional Context
              </label>
              <textarea
                value={lessonContext}
                onChange={(event) => onLessonContextChange(event.target.value)}
                rows={3}
                className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
              />
            </div>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <label className="text-xs font-semibold text-ink-700 mb-1 block">
                  Lesson Duration
                </label>
                <select
                  value={lessonDuration}
                  onChange={(event) => onLessonDurationChange(event.target.value)}
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
                >
                  <option>30 minutes</option>
                  <option>45 minutes</option>
                  <option>60 minutes</option>
                  <option>90 minutes</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-ink-700 mb-1 block">Class Size</label>
                <input
                  type="number"
                  value={classSize}
                  onChange={(event) => onClassSizeChange(event.target.value)}
                  className="w-full border border-ink-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink-500 bg-parchment-50 text-ink-800"
                  placeholder="e.g., 25"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="workspace-card p-3 space-y-3">
          <div>
            <p className="text-xs uppercase tracking-wider text-ink-600 mb-2">Session Pulse</p>
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-ink-800 truncate">{sessionStatusLabel}</p>
                <p className="text-xs text-ink-600 truncate">
                  {session
                    ? 'Ready to receive your next prompt'
                    : sessionError
                    ? 'This workspace needs attention'
                    : 'AI is initializing'}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {sessionError && onRetrySession && (
                  <button
                    onClick={onRetrySession}
                    disabled={isRetryingSession}
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border transition-colors ${
                      isRetryingSession
                        ? 'bg-ink-300 text-ink-500 border-ink-400 cursor-not-allowed'
                        : 'bg-ink-600 text-parchment-100 border-ink-700 hover:bg-ink-700 cursor-pointer'
                    }`}
                  >
                    {isRetryingSession ? 'Retrying...' : 'Retry'}
                  </button>
                )}
                {!sessionError || !onRetrySession ? (
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border flex-shrink-0 ${sessionStatusTone}`}
                  >
                    {sessionStatusDetail}
                  </span>
                ) : null}
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-ink-600">
              <span>Mode</span>
              <span className="capitalize">{mode}</span>
            </div>
          </div>

          <div className="border-t border-ink-300 pt-3">
            <h3 className="font-semibold text-ink-800 mb-2 text-xs">Your Activity</h3>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={onViewMessages}
                disabled={!onViewMessages || messageCount === 0}
                className={`bg-gradient-to-br from-parchment-200 to-parchment-300 rounded-lg p-2 border border-ink-300 text-left transition-colors ${
                  onViewMessages && messageCount > 0
                    ? 'hover:from-parchment-300 hover:to-parchment-400 hover:border-ink-400 cursor-pointer'
                    : 'cursor-default'
                } ${!onViewMessages || messageCount === 0 ? 'opacity-60' : ''}`}
                title={messageCount > 0 ? `View ${messageCount} message${messageCount !== 1 ? 's' : ''} in chat` : 'No messages available'}
              >
                <div className="text-lg font-bold text-ink-700">{messageCount}</div>
                <div className="text-xs text-ink-600 leading-tight">Messages</div>
              </button>
              <button
                onClick={onViewConversations}
                disabled={!onViewConversations || lessonsCount === 0}
                className={`bg-gradient-to-br from-parchment-200 to-parchment-300 rounded-lg p-2 border border-ink-300 text-left transition-colors ${
                  onViewConversations && lessonsCount > 0
                    ? 'hover:from-parchment-300 hover:to-parchment-400 hover:border-ink-400 cursor-pointer'
                    : 'cursor-default'
                } ${!onViewConversations || lessonsCount === 0 ? 'opacity-60' : ''}`}
                title={lessonsCount > 0 ? `View ${lessonsCount} lesson${lessonsCount !== 1 ? 's' : ''} in sidebar` : 'No lessons available'}
              >
                <div className="text-lg font-bold text-ink-700">{lessonsCount}</div>
                <div className="text-xs text-ink-600 leading-tight">Lessons</div>
              </button>
              <button
                onClick={onViewDrafts}
                disabled={!onViewDrafts || draftCount === 0}
                className={`bg-gradient-to-br from-parchment-200 to-parchment-300 rounded-lg p-2 border border-ink-300 text-left transition-colors ${
                  onViewDrafts && draftCount > 0
                    ? 'hover:from-parchment-300 hover:to-parchment-400 hover:border-ink-400 cursor-pointer'
                    : 'cursor-default'
                } ${!onViewDrafts || draftCount === 0 ? 'opacity-60' : ''}`}
                title={draftCount > 0 ? `View ${draftCount} draft${draftCount !== 1 ? 's' : ''}` : 'No drafts available'}
              >
                <div className="text-lg font-bold text-ink-600">{draftCount}</div>
                <div className="text-xs text-ink-600 leading-tight">Drafts</div>
              </button>
            </div>
            <div className="mt-2 text-xs text-ink-600 leading-tight">
              <span>{storageInfo?.image_count ?? 0} images</span>
              <span className="mx-1">•</span>
              <span>Demo mode</span>
            </div>
          </div>

          {/* Retry Feedback */}
          {retrySuccess !== null && retryMessage && (
            <div
              className={`p-3 rounded-lg border text-sm ${
                retrySuccess
                  ? 'bg-green-50 text-green-800 border-green-200'
                  : 'bg-red-50 text-red-800 border-red-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <svg
                  className={`w-4 h-4 flex-shrink-0 ${
                    retrySuccess ? 'text-green-600' : 'text-red-600'
                  }`}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  {retrySuccess ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  )}
                </svg>
                <span className="flex-1">{retryMessage}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
