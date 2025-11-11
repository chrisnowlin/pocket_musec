import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  ChangeEvent,
  DragEvent,
  FormEvent,
  MouseEvent as ReactMouseEvent,
} from 'react';
import api from '../lib/api';
import type {
  StandardRecord,
  SessionResponsePayload,
  ChatResponsePayload,
} from '../lib/types';
import DocumentIngestion from '../components/DocumentIngestion';
import IngestionStatus from '../components/IngestionStatus';

type PanelSide = 'sidebar' | 'right';
type ChatSender = 'user' | 'ai';
type ViewMode = 'chat' | 'browse' | 'ingestion' | 'images' | 'settings';

interface ChatMessage {
  id: string;
  sender: ChatSender;
  text: string;
  timestamp: string;
}

interface ImageData {
  id: string;
  filename: string;
  uploaded_at: string;
  ocr_text?: string | null;
  vision_analysis?: string | null;
  file_size: number;
  mime_type: string;
}

interface StorageInfo {
  image_count: number;
  usage_mb: number;
  limit_mb: number;
  available_mb: number;
  percentage: number;
}

const gradeOptions = [
  'Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8',
];

const strandOptions = ['Connect', 'Create', 'Respond', 'Present'];

const standardLibrary: StandardRecord[] = [
  {
    id: 'cn-3-1',
    code: '3.CN.1',
    strand_code: 'CN',
    strand_name: 'Connect',
    grade: 'Grade 3',
    title: 'Understand relationships between music, other disciplines, and daily life',
    description: 'Students explore how music relates to other subjects, cultures, and real‑world experiences.',
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
    description: 'Students discover musical ideas across cultures and link them to science, history, and language.',
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
    description: 'Students improvise and notate ideas that incorporate steady beat and contrasting dynamics.',
    objectives: 5,
    last_used: '1 week ago',
    learningObjectives: [
      'Write rhythm patterns with quarter and eighth notes.',
      'Layer dynamics to create contrast.',
      'Perform composition with peers.',
    ],
  },
];

const conversationGroups = [
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

const quickAccessLinks = [
  { label: 'Templates', hint: 'Saved song maps' },
  { label: 'Saved Drafts', hint: '8 drafts' },
];

const quickStats = {
  lessonsCreated: 23,
  activeDrafts: 8,
};

export default function UnifiedPage() {
  const [mode, setMode] = useState<ViewMode>('chat');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [session, setSession] = useState<SessionResponsePayload | null>(null);
  const [standards, setStandards] = useState<StandardRecord[]>(standardLibrary);
  const [selectedStandard, setSelectedStandard] = useState<StandardRecord | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [selectedGrade, setSelectedGrade] = useState('Grade 3');
  const [selectedStrand, setSelectedStrand] = useState('Connect');
  const [lessonContext, setLessonContext] = useState('Class has recorders and a 30-minute block with mixed instruments.');
  const [lessonDuration, setLessonDuration] = useState('30 minutes');
  const [classSize, setClassSize] = useState('25');
  const [browseQuery, setBrowseQuery] = useState('');
  const [sidebarWidth, setSidebarWidth] = useState(256);
  const [rightPanelWidth, setRightPanelWidth] = useState(384);
  const [resizingPanel, setResizingPanel] = useState<PanelSide | null>(null);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);
  
  // Image processing states
  const [images, setImages] = useState<ImageData[]>([]);
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [imageDragActive, setImageDragActive] = useState(false);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  
  // Settings states
  const [currentProcessingMode, setCurrentProcessingMode] = useState('cloud');

  const messageContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const appendMessage = useCallback((sender: ChatSender, text: string, id?: string) => {
    const messageId = id ?? `${sender}-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: messageId,
        sender,
        text,
        timestamp: new Date().toISOString(),
      },
    ]);
    return messageId;
  }, []);

  const updateMessageText = useCallback((id: string, updater: (current: string) => string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === id ? { ...message, text: updater(message.text) } : message
      )
    );
  }, []);

  const processChatMessage = useCallback(
    async (messageText: string) => {
      const activeSessionId = session?.id;
      if (!activeSessionId) {
        setChatError('Start a session before chatting with the AI.');
        return;
      }

      setIsTyping(true);
      setChatError(null);

      const aiMessageId = appendMessage('ai', '');

      try {
        const response = await api.streamChatMessage(activeSessionId, {
          message: messageText,
          lesson_duration: lessonDuration,
          class_size: classSize,
        });

        if (!response.ok || !response.body) {
          throw new Error('Streaming is unavailable.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let boundary = buffer.indexOf('\n\n');
          while (boundary !== -1) {
            const chunk = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            if (chunk.startsWith('data:')) {
              const payload = chunk.replace(/^data:\s*/, '');
              if (payload && payload !== '[DONE]') {
                try {
                  const event = JSON.parse(payload);
                  if (event.type === 'delta' && event.text) {
                    updateMessageText(aiMessageId, (current) => `${current} ${event.text}`.trim());
                  } else if (event.type === 'status' && event.message) {
                    updateMessageText(aiMessageId, () => event.message);
                  } else if (event.type === 'complete') {
                    const payloadData = event.payload as ChatResponsePayload;
                    updateMessageText(aiMessageId, () => payloadData.response);
                    setSession(payloadData.session);
                  }
                } catch (err) {
                  console.error('Failed to parse stream event', err);
                }
              }
            }
            boundary = buffer.indexOf('\n\n');
          }
        }
      } catch (err: any) {
        console.error('Chat message failed:', err);
        setChatError(err.message || 'Failed to send your message');
        updateMessageText(aiMessageId, () => 'Sorry, I could not generate a response.');
      } finally {
        setIsTyping(false);
      }
    },
    [session?.id, lessonDuration, classSize, appendMessage, updateMessageText]
  );

  const sendMessage = () => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;

    appendMessage('user', trimmed);
    setChatInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    processChatMessage(trimmed);
  };

  const loadStandards = useCallback(
    async (grade: string, strand: string) => {
      try {
        const result = await api.listStandards({
          grade_level: grade,
          strand_code: strand,
        });

        if (result.ok) {
          const payload = result.data;
          setStandards(payload.length ? payload : standardLibrary);
        }
      } catch (err) {
        console.error('Failed to load standards', err);
      }
    },
    []
  );

  const initSession = useCallback(async () => {
    const defaultGrade = 'Grade 3';
    const defaultStrand = 'Connect';

    try {
      const result = await api.createSession({
        grade_level: defaultGrade,
        strand_code: defaultStrand,
      });

      if (result.ok) {
        setSession(result.data);
        setSelectedGrade(result.data.grade_level ?? defaultGrade);
        setSelectedStrand(result.data.strand_code ?? defaultStrand);
        if (result.data.selected_standard) {
          setSelectedStandard(result.data.selected_standard);
        }
        await loadStandards(
          result.data.grade_level ?? defaultGrade,
          result.data.strand_code ?? defaultStrand
        );
      } else {
        setSessionError(result.message || 'Unable to start a session');
      }
    } catch (err: any) {
      console.error('Failed to initialize session', err);
      setSessionError(err.message || 'Unable to start a session');
    }
  }, [loadStandards]);

  useEffect(() => {
    initSession();
  }, [initSession]);

  // Image processing functions
  const loadImages = useCallback(async () => {
    try {
      const result = await api.getImages();
      if (result.ok) {
        setImages(result.data as ImageData[]);
      } else {
        setUploadError(result.message || 'Unable to load images');
      }
    } catch (err: any) {
      console.error('Failed to load images', err);
      setUploadError(err.message || 'Unable to load images');
    }
  }, []);

  const loadStorageInfo = useCallback(async () => {
    try {
      const result = await api.getImageStorageInfo();
      if (result.ok) {
        const data = result.data as StorageInfo;
        setStorageInfo(data);
      }
    } catch (err) {
      console.error('Failed to load storage info', err);
    }
  }, []);

  const uploadFiles = async (files: File[]) => {
    if (!files.length) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(0);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('analyze_vision', 'true');

    try {
      const result = await api.uploadImages(formData, (progress) => {
        setUploadProgress(progress);
      });

      if (result.ok) {
        await loadImages();
        await loadStorageInfo();
      } else {
        setUploadError(result.message || 'Upload failed');
      }
    } catch (err: any) {
      console.error('Upload failed', err);
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length) {
      uploadFiles(Array.from(files));
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setImageDragActive(false);
    const files = Array.from(event.dataTransfer.files).filter((file) =>
      file.type.startsWith('image/')
    );
    if (files.length) {
      uploadFiles(files);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    try {
      const result = await api.deleteImage(imageId);
      if (result.ok) {
        await loadImages();
        await loadStorageInfo();
        if (selectedImage?.id === imageId) {
          setSelectedImage(null);
        }
      } else {
        setUploadError(result.message || 'Failed to delete image');
      }
    } catch (err: any) {
      console.error('Failed to delete image', err);
      setUploadError(err.message || 'Failed to delete image');
    }
  };

  const handleResizerMouseDown = (panel: PanelSide, event: ReactMouseEvent<HTMLDivElement>) => {
    setResizingPanel(panel);
    setStartX(event.clientX);
    setStartWidth(panel === 'sidebar' ? sidebarWidth : rightPanelWidth);
    event.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!resizingPanel) return;
      if (resizingPanel === 'sidebar') {
        const delta = event.clientX - startX;
        const width = Math.min(Math.max(startWidth + delta, 200), 400);
        setSidebarWidth(width);
      } else if (resizingPanel === 'right') {
        const delta = event.clientX - startX;
        const width = Math.min(Math.max(startWidth - delta, 300), 600);
        setRightPanelWidth(width);
      }
    };

    const handleMouseUp = () => {
      setResizingPanel(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizingPanel, startX, startWidth]);

  useEffect(() => {
    document.body.classList.toggle('no-select', Boolean(resizingPanel));
  }, [resizingPanel]);

  useEffect(() => {
    loadImages();
    loadStorageInfo();
  }, [loadImages, loadStorageInfo]);

  useEffect(() => {
    if (messageContainerRef.current) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const filteredStandards = useMemo(() => {
    return standards.filter((standard) => {
      const matchesGrade = selectedGrade ? standard.grade === selectedGrade : true;
      const matchesStrand = selectedStrand ? standard.strand_name === selectedStrand : true;
      const matchesSearch = browseQuery
        ? standard.title.toLowerCase().includes(browseQuery.toLowerCase()) ||
          standard.description.toLowerCase().includes(browseQuery.toLowerCase()) ||
          standard.code.toLowerCase().includes(browseQuery.toLowerCase())
        : true;
      return matchesGrade && matchesStrand && matchesSearch;
    });
  }, [browseQuery, selectedGrade, selectedStrand, standards]);

  const recentImages = useMemo(() => images.slice(0, 3), [images]);

  const handleTextareaInput = (event: FormEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    target.style.height = 'auto';
    target.style.height = `${Math.min(target.scrollHeight, 180)}px`;
  };

  const heroFocusTitle = selectedStandard
    ? `${selectedStandard.code} · ${selectedStandard.title}`
    : 'Guide a new lesson with PocketMusec';
  const heroFocusSubtitle = selectedStandard?.description ?? 'Select a standard or describe your lesson so the AI can help.';
  const heroBadges = [
    { label: selectedGrade || 'Grade level', id: 'grade' },
    { label: selectedStrand || 'Strand', id: 'strand' },
    { label: lessonDuration, id: 'duration' },
    { label: `${classSize} students`, id: 'class-size' },
  ];
  const sessionStatusLabel = session
    ? 'Connected to PocketMusec'
    : sessionError
    ? 'Session not responding'
    : 'Waking up the AI';
  const sessionStatusTone = session
    ? 'bg-emerald-100 text-emerald-900 border-emerald-200'
    : sessionError
    ? 'bg-rose-100 text-rose-900 border-rose-200'
    : 'bg-amber-100 text-amber-900 border-amber-200';
  const sessionStatusDetail = session ? 'Live' : sessionError ? 'Retry' : 'Loading';
  const chatProgress = Math.min(messages.length * 5, 100);

  return (
    <>
      <div className="flex h-screen">
        {/* Sidebar */}
        <aside
          id="sidebar"
          className="bg-gray-900 text-white flex flex-col panel overflow-hidden"
          style={{ width: `${sidebarWidth}px`, minWidth: '200px', maxWidth: '400px' }}
        >
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                  />
                </svg>
              </div>
              <div>
                <h1 className="font-bold">PocketMusec</h1>
                <p className="text-xs text-gray-400">AI Assistant</p>
              </div>
            </div>
            <button
              onClick={() => {
                setMessages([
                  {
                    id: 'welcome',
                    sender: 'ai',
                    text: "👋 Welcome! I'm your PocketMusec AI assistant. I'll help you craft engaging, standards-aligned music lessons.",
                    timestamp: new Date().toISOString(),
                  },
                ]);
                setSelectedGrade('Grade 3');
                setSelectedStandard(standards[0] ?? standardLibrary[0]);
                setSelectedStrand('Connect');
                setMode('chat');
              }}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Conversation
            </button>
          </div>

          <div className="p-3 border-b border-gray-700">
            <div className="bg-gray-800 rounded-lg p-1 flex flex-wrap gap-1">
              {(['chat', 'browse', 'ingestion', 'images', 'settings'] as ViewMode[]).map((viewMode) => (
                <button
                  key={viewMode}
                  onClick={() => setMode(viewMode)}
                  className={`flex-1 px-2 py-1.5 text-xs font-medium rounded capitalize ${
                    mode === viewMode
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white transition-colors'
                  }`}
                >
                  {viewMode}
                </button>
              ))}
            </div>
          </div>

          <nav className="flex-1 scrollable p-3 space-y-1">
            {mode === 'chat' && conversationGroups.map((group) => (
              <div key={group.label} className="mb-4">
                <h3 className="px-3 text-xs font-semibold text-gray-400 uppercase mb-2">
                  {group.label}
                </h3>
                <div className="space-y-1">
                  {group.items.map((item) => (
                    <button
                      key={item.title}
                      className={`w-full text-left px-3 py-2 rounded-lg ${
                        item.active ? 'bg-gray-800 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                      }`}
                    >
                      <div className="text-sm font-medium truncate">{item.title}</div>
                      <div className="text-xs text-gray-500">{item.hint}</div>
                    </button>
                  ))}
                </div>
              </div>
            ))}

            <div className="pt-4 mt-4 border-t border-gray-700">
              <h3 className="px-3 text-xs font-semibold text-gray-400 uppercase mb-2">Quick Access</h3>
              <div className="space-y-1">
                {quickAccessLinks.map((link) => (
                  <button
                    key={link.label}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white w-full"
                  >
                    <span className="text-sm">{link.label}</span>
                    <span className="ml-auto text-xs text-gray-500">{link.hint}</span>
                  </button>
                ))}
              </div>
            </div>
          </nav>

          <div className="p-3 border-t border-gray-700">
            <div className="text-xs text-gray-400 px-3 py-2">
              <p>Demo Environment</p>
              <p>Single-user mode</p>
            </div>
          </div>
        </aside>

        <div
          id="sidebarResizer"
          className={`resizer ${resizingPanel === 'sidebar' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('sidebar', event)}
        />

        {/* Main Content */}
        <section className="flex-1 flex flex-col panel workspace-panel-glass">
          <div className="px-6 pt-6 pb-4">
            <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
              <div className="rounded-2xl bg-gradient-to-r from-purple-600 to-sky-500 p-6 text-white shadow-2xl overflow-hidden">
                <p className="text-xs uppercase tracking-[0.4em] text-white/80">Current Focus</p>
                <h3 className="mt-3 text-xl font-semibold leading-tight">{heroFocusTitle}</h3>
                <p className="mt-2 text-sm text-white/90">{heroFocusSubtitle}</p>
                <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
                  {heroBadges.map((badge) => (
                    <span key={badge.id} className="rounded-full border border-white/40 bg-white/15 px-3 py-1">
                      {badge.label}
                    </span>
                  ))}
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs text-white/70">
                  <span className="inline-flex h-3 w-3 rounded-full bg-white animate-pulse" />
                  <span>
                    {session
                      ? 'Learning session live'
                      : sessionError
                      ? 'Waiting on your last request'
                      : 'Preparing PocketMusec AI'}
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="workspace-card p-4">
                  <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Session Pulse</p>
                  <div className="mt-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-lg font-semibold text-gray-900">{sessionStatusLabel}</p>
                      <p className="text-xs text-gray-500">
                        {session
                          ? 'Ready to receive your next prompt'
                          : sessionError
                          ? 'This workspace needs attention'
                          : 'AI is initializing'}
                      </p>
                    </div>
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${sessionStatusTone}`}>
                      {sessionStatusDetail}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                    <span>Mode</span>
                    <span className="capitalize">{mode}</span>
                  </div>
                </div>
                <div className="workspace-card p-4">
                  <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Activity</p>
                  <div className="mt-3 flex items-center justify-between">
                    <div>
                      <p className="text-2xl font-semibold text-gray-900">{messages.length}</p>
                      <p className="text-xs text-gray-500">Messages this session</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-semibold text-purple-600">{quickStats.lessonsCreated}</p>
                      <p className="text-xs text-gray-500">Lessons created</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Content Area */}
          <div className="flex-1 overflow-hidden">
            {mode === 'chat' && (
              <div className="h-full flex flex-col">
                <div className="border-b border-gray-200 bg-white px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">Lesson Planning Chat</h2>
                      <p className="text-sm text-gray-500">Conversational AI guidance</p>
                    </div>
                  </div>
                </div>

                <div className="px-6 pb-4">
                  <div className="workspace-card p-4 space-y-3">
                    <p className="text-xs uppercase tracking-wider text-gray-500">Quick grade entry</p>
                    <div className="grid grid-cols-3 gap-2">
                      {gradeOptions.map((grade) => (
                        <button
                          key={grade}
                          onClick={() => setSelectedGrade(grade)}
                          className={`text-xs font-medium px-3 py-2 rounded-lg border transition ${
                            selectedGrade === grade
                              ? 'border-purple-500 bg-purple-50 text-purple-700'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-purple-300 hover:bg-purple-50'
                          }`}
                        >
                          {grade}
                        </button>
                      ))}
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {strandOptions.map((strand) => (
                        <button
                          key={strand}
                          onClick={() => setSelectedStrand(strand)}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-full border ${
                            selectedStrand === strand
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-gray-200 text-gray-600 hover:border-blue-300'
                          }`}
                        >
                          {strand}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div
                  ref={messageContainerRef}
                  className="flex-1 scrollable px-6 py-4 space-y-4 workspace-card"
                >
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 items-start ${
                        message.sender === 'user' ? 'justify-end' : ''
                      }`}
                    >
                      {message.sender === 'ai' && (
                        <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                            />
                          </svg>
                        </div>
                      )}
                      <div className="flex-1 max-w-3xl">
                        <div
                          className={`flex items-center gap-2 mb-2 ${
                            message.sender === 'user' ? 'justify-end' : ''
                          }`}
                        >
                          <span className="text-xs font-semibold text-gray-700">
                            {message.sender === 'ai' ? 'PocketMusec AI' : 'You'}
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">Just now</span>
                        </div>
                        <div
                          className={`rounded-lg shadow-sm border px-4 py-3 ${
                            message.sender === 'ai'
                              ? 'bg-white border-gray-200 text-gray-700'
                              : 'bg-purple-600 text-white'
                          }`}
                        >
                          <p className="text-sm leading-relaxed">{message.text}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="flex items-center gap-2">
                      <div className="typing-indicator flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-gray-400" />
                        <span className="w-2.5 h-2.5 rounded-full bg-gray-400" />
                        <span className="w-2.5 h-2.5 rounded-full bg-gray-400" />
                      </div>
                      <span className="text-xs text-gray-500">PocketMusec is typing...</span>
                    </div>
                  )}
                </div>

                <div className="border-t border-gray-200 px-6 py-4">
                  <div className="workspace-card p-4 space-y-3">
                    <div className="flex gap-3 items-end">
                      <div className="flex-1 relative">
                        <textarea
                          ref={textareaRef}
                          value={chatInput}
                          onChange={(event) => setChatInput(event.target.value)}
                          onInput={handleTextareaInput}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' && !event.shiftKey) {
                              event.preventDefault();
                              sendMessage();
                            }
                          }}
                          className="w-full border border-gray-200 rounded-xl px-4 py-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                          rows={1}
                          placeholder="Type a message or use the buttons above..."
                        />
                        <button className="absolute right-3 bottom-3 text-gray-400 hover:text-gray-600 transition-colors">
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                            />
                          </svg>
                        </button>
                      </div>
                      <button
                        onClick={sendMessage}
                        className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-6 py-3 font-medium transition-colors shadow-sm"
                      >
                        Send
                      </button>
                    </div>
                    {sessionError && (
                      <div className="mt-2 rounded-md bg-yellow-50 px-3 py-2 text-xs text-yellow-800">
                        {sessionError}
                      </div>
                    )}
                    {chatError && (
                      <div className="mt-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
                        {chatError}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {mode === 'browse' && (
              <div className="h-full flex flex-col">
                <div className="px-6 pb-4">
                  <div className="workspace-card p-4 space-y-3">
                    <div className="flex items-center gap-4 mb-3">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          placeholder="Search standards, objectives, or topics..."
                          value={browseQuery}
                          onChange={(event) => setBrowseQuery(event.target.value)}
                          className="w-full border border-gray-300 rounded-lg px-4 py-2 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                        <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {gradeOptions.slice(0, 5).map((grade) => (
                        <button
                          key={grade}
                          onClick={() => setSelectedGrade(grade)}
                          className={`px-3 py-1 text-xs font-medium rounded-full border ${
                            selectedGrade === grade
                              ? 'bg-purple-100 text-purple-700 border-purple-200'
                              : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          {grade}
                        </button>
                      ))}
                      <div className="border-l border-gray-300 mx-2" />
                      {strandOptions.map((strand) => (
                        <button
                          key={strand}
                          onClick={() => setSelectedStrand(strand)}
                          className={`px-3 py-1 text-xs font-medium rounded-full border ${
                            selectedStrand === strand
                              ? 'bg-blue-100 text-blue-700 border-blue-200'
                              : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          {strand}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex-1 scrollable px-6 pb-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-semibold text-gray-900">
                        Standards for {selectedGrade} · {selectedStrand}
                      </h2>
                      <span className="text-sm text-gray-500">{filteredStandards.length} standards found</span>
                    </div>
                    <div className="space-y-3">
                      {filteredStandards.map((standard) => (
                        <div
                          key={standard.id}
                          className={`border ${
                            selectedStandard?.id === standard.id
                              ? 'border-blue-300 bg-blue-50'
                              : 'border-gray-200 bg-white'
                          } rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors`}
                          onClick={() => setSelectedStandard(standard)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs font-mono font-semibold text-gray-700 bg-gray-100 px-2 py-1 rounded">
                                  {standard.code}
                                </span>
                                <span className="text-xs text-gray-500">{standard.strand_name} Strand</span>
                              </div>
                              <h3 className="font-medium text-gray-900 mb-2">{standard.title}</h3>
                              <div className="flex items-center gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1">
                                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                  </svg>
                                  {standard.objectives} objectives
                                </span>
                                <span className="flex items-center gap-1">
                                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  {standard.last_used ?? 'Recently used'}
                                </span>
                              </div>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setMode('chat');
                                const prompt = `Start crafting a lesson centered on ${standard.code} - ${standard.title}`;
                                appendMessage('user', prompt);
                                processChatMessage(prompt);
                              }}
                              className={`text-sm font-medium ml-4 whitespace-nowrap ${
                                selectedStandard?.id === standard.id
                                  ? 'text-blue-600 hover:text-blue-700'
                                  : 'text-purple-600 hover:text-purple-700'
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
            )}

            {mode === 'ingestion' && (
              <div className="h-full overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Document Ingestion</h2>
                    <p className="text-gray-600 mt-2">
                      Upload and process music education documents with AI-powered analysis
                    </p>
                  </div>
                  <DocumentIngestion onIngestionComplete={() => {}} />
                  <div className="mt-8">
                    <IngestionStatus />
                  </div>
                </div>
              </div>
            )}

            {mode === 'images' && (
              <div className="h-full overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Image Processing</h2>
                    <p className="text-gray-600 mt-2">
                      Upload sheet music, diagrams, and other images for OCR and AI analysis
                    </p>
                  </div>

                  {/* Storage Info */}
                  {storageInfo && (
                    <div className="bg-white shadow rounded-lg p-6 mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Usage</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Images:</span>
                          <span className="font-medium">{storageInfo.image_count}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Storage:</span>
                          <span className="font-medium">
                            {storageInfo.usage_mb.toFixed(2)} MB / {storageInfo.limit_mb} MB
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className={`h-2.5 rounded-full ${
                              storageInfo.percentage > 90
                                ? 'bg-red-600'
                                : storageInfo.percentage > 70
                                ? 'bg-yellow-600'
                                : 'bg-blue-600'
                            }`}
                            style={{ width: `${Math.min(storageInfo.percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Upload Area */}
                  <div
                    className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors mb-6 ${
                      imageDragActive
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setImageDragActive(true);
                    }}
                    onDragLeave={(e) => {
                      e.preventDefault();
                      setImageDragActive(false);
                    }}
                    onDrop={handleDrop}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept="image/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />

                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>

                    <p className="mt-4 text-lg text-gray-600">
                      Drag and drop images here, or{' '}
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        browse files
                      </button>
                    </p>
                    <p className="mt-2 text-sm text-gray-500">
                      Supports PNG, JPEG, GIF, WebP (max 10MB per file)
                    </p>

                    {isUploading && (
                      <div className="mt-6 max-w-md mx-auto">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className="bg-blue-600 h-2.5 rounded-full transition-all"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                        <p className="mt-2 text-sm text-gray-600">Uploading... {uploadProgress}%</p>
                      </div>
                    )}
                  </div>

                  {uploadError && (
                    <div className="rounded-md bg-red-50 p-4 mb-6">
                      <div className="text-sm text-red-800">{uploadError}</div>
                    </div>
                  )}

                  {/* Recent Images */}
                  {recentImages.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Images</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {recentImages.map((image) => (
                          <div
                            key={image.id}
                            className="bg-white shadow rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                            onClick={() => setSelectedImage(image)}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900 truncate">{image.filename}</h4>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteImage(image.id);
                                }}
                                className="text-red-600 hover:text-red-700"
                              >
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                            <p className="text-sm text-gray-600">
                              {new Date(image.uploaded_at).toLocaleDateString()}
                            </p>
                            {image.ocr_text && (
                              <p className="text-sm text-gray-700 mt-2 line-clamp-2">{image.ocr_text}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {mode === 'settings' && (
              <div className="h-full overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
                    <p className="text-gray-600 mt-2">
                      Configure your processing preferences and system settings
                    </p>
                  </div>

                  <div className="space-y-6">
                    {/* Account Information */}
                    <div className="bg-white shadow rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Name:</span>
                          <span className="font-medium">Demo User</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Email:</span>
                          <span className="font-medium">demo@example.com</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Role:</span>
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800 capitalize">
                            Admin
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Processing Mode */}
                    <div className="bg-white shadow rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Mode</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        Choose how AI processing is performed for lesson generation and image analysis
                      </p>
                      <div className="space-y-3">
                        <div className={`border-2 rounded-lg p-4 ${
                          currentProcessingMode === 'cloud' ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        }`}>
                          <div className="flex items-center">
                            <input
                              type="radio"
                              name="processing_mode"
                              checked={currentProcessingMode === 'cloud'}
                              onChange={() => setCurrentProcessingMode('cloud')}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <label className="ml-3">
                              <span className="text-lg font-medium text-gray-900">Cloud Mode</span>
                              {currentProcessingMode === 'cloud' && (
                                <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-600 text-white">
                                  Current
                                </span>
                              )}
                            </label>
                          </div>
                          <p className="ml-7 mt-2 text-sm text-gray-600">
                            Fast processing with cloud AI API. No local setup required.
                          </p>
                        </div>
                        <div className={`border-2 rounded-lg p-4 ${
                          currentProcessingMode === 'local' ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        }`}>
                          <div className="flex items-center">
                            <input
                              type="radio"
                              name="processing_mode"
                              checked={currentProcessingMode === 'local'}
                              onChange={() => setCurrentProcessingMode('local')}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <label className="ml-3">
                              <span className="text-lg font-medium text-gray-900">Local Mode</span>
                              {currentProcessingMode === 'local' && (
                                <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-600 text-white">
                                  Current
                                </span>
                              )}
                            </label>
                          </div>
                          <p className="ml-7 mt-2 text-sm text-gray-600">
                            Private processing with local AI model. Data stays on your machine.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* System Status */}
                    <div className="bg-white shadow rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Backend API:</span>
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Connected
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Database:</span>
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Ready
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">AI Services:</span>
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Online
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        <div
          id="rightPanelResizer"
          className={`resizer ${resizingPanel === 'right' ? 'resizing' : ''}`}
          onMouseDown={(event) => handleResizerMouseDown('right', event)}
        />

        {/* Right Panel */}
        <aside
          id="rightPanel"
          className="border-l border-gray-200 flex flex-col panel workspace-panel-glass"
          style={{ width: `${rightPanelWidth}px`, minWidth: '300px', maxWidth: '600px' }}
        >
          <div className="border-b border-gray-200 bg-white px-6 py-4">
            <h2 className="font-semibold text-gray-900">Context & Configuration</h2>
            <p className="text-xs text-gray-500 mt-1">Lesson settings, processing options, and assets</p>
          </div>

          <div className="flex-1 scrollable p-6 space-y-4">
            <div className="workspace-card p-4 space-y-3">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Current Selections
              </h3>
              <div className="space-y-3 text-sm text-gray-700">
                <div className="flex justify-between">
                  <span>Grade Level</span>
                  <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-700 border border-purple-200">
                    {selectedGrade}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Strand</span>
                  <span className="italic text-gray-500">{selectedStrand || 'Not selected yet'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Standard</span>
                  <span className="italic text-gray-500">
                    {selectedStandard?.code ?? 'Not selected yet'}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setMode('browse')}
                className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Browse Standards
              </button>
            </div>

            <div className="workspace-card p-4 space-y-3">
              <h3 className="font-semibold text-gray-900">Lesson Settings</h3>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Additional Context</label>
                <textarea
                  value={lessonContext}
                  onChange={(event) => setLessonContext(event.target.value)}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-gray-700 mb-1 block">Lesson Duration</label>
                  <select
                    value={lessonDuration}
                    onChange={(event) => setLessonDuration(event.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option>30 minutes</option>
                    <option>45 minutes</option>
                    <option>60 minutes</option>
                    <option>90 minutes</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-700 mb-1 block">Class Size</label>
                  <input
                    type="number"
                    value={classSize}
                    onChange={(event) => setClassSize(event.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., 25"
                  />
                </div>
              </div>
            </div>

            {selectedStandard && (
              <div className="workspace-card p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">
                    {selectedStandard.code}
                  </span>
                  <span className="text-xs text-gray-500">
                    {selectedStandard.grade} • {selectedStandard.strand_name}
                  </span>
                </div>
                <h3 className="font-medium text-gray-900">{selectedStandard.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{selectedStandard.description}</p>
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 uppercase mb-1">Learning Objectives</h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    {selectedStandard.learningObjectives.map((objective) => (
                      <li className="flex items-start gap-2" key={objective}>
                        <svg className="w-4 h-4 text-green-600 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span>{objective}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="workspace-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Quick Actions</h3>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => setMode('ingestion')}
                  className="w-full px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm"
                >
                  📄 Upload Documents
                </button>
                <button
                  onClick={() => setImageModalOpen(true)}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  🖼️ Upload Images
                </button>
                <button
                  onClick={() => setMode('settings')}
                  className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
                >
                  ⚙️ Settings
                </button>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl border border-purple-200 p-4 shadow-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Your Activity</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3">
                  <div className="text-2xl font-bold text-purple-600">{quickStats.lessonsCreated}</div>
                  <div className="text-xs text-gray-600">Lessons Created</div>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <div className="text-2xl font-bold text-blue-600">{quickStats.activeDrafts}</div>
                  <div className="text-xs text-gray-600">Active Drafts</div>
                </div>
              </div>
              <div className="mt-3 text-xs text-gray-600">
                <p>{storageInfo?.image_count ?? 0} images stored</p>
                <p>Demo environment • single-user mode</p>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Image Upload Modal */}
      {imageModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => {
            setImageModalOpen(false);
            setImageDragActive(false);
          }}
        >
          <div
            className="bg-white rounded-2xl max-w-3xl w-full p-6 shadow-xl space-y-4"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Upload Images</h3>
              <button
                onClick={() => {
                  setImageModalOpen(false);
                  setImageDragActive(false);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div
              className={`border-2 rounded-2xl p-8 text-center transition-colors ${
                imageDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-dashed border-gray-300 bg-white'
              }`}
              onDragOver={(event) => {
                event.preventDefault();
                setImageDragActive(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                setImageDragActive(false);
              }}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleFileSelect}
              />
              <svg className="mx-auto h-12 w-12 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-4 text-lg text-gray-600">
                Drag and drop images or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  browse files
                </button>
              </p>
              <p className="mt-2 text-xs text-gray-500">PNG, JPEG, TIFF, WebP (max 10MB per file)</p>
              {isUploading && (
                <div className="mt-6">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className="h-2.5 rounded-full bg-blue-600 transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Uploading — {uploadProgress}% complete
                  </p>
                </div>
              )}
            </div>
            {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setImageModalOpen(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Browse Files
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Detail Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-2xl font-bold text-gray-900">{selectedImage.filename}</h3>
              <button onClick={() => setSelectedImage(null)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="space-y-4 text-sm text-gray-600">
              <p>Uploaded: {new Date(selectedImage.uploaded_at).toLocaleString()}</p>
              <p>Size: {(selectedImage.file_size / 1024).toFixed(2)} KB</p>
              <p>Type: {selectedImage.mime_type}</p>
              {selectedImage.ocr_text && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">OCR Extracted Text</h4>
                  <div className="bg-gray-50 rounded p-4 text-sm text-gray-700 whitespace-pre-wrap">
                    {selectedImage.ocr_text}
                  </div>
                </div>
              )}
              {selectedImage.vision_analysis && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Vision Analysis</h4>
                  <div className="bg-blue-50 rounded p-4 text-sm text-gray-700 whitespace-pre-wrap">
                    {selectedImage.vision_analysis}
                  </div>
                </div>
              )}
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => handleDeleteImage(selectedImage.id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  Delete
                </button>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}