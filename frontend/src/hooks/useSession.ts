import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { SessionResponsePayload, StandardRecord } from '../lib/types';
import type { ConversationGroup, ConversationItem } from '../types/unified';
import { standardLibrary } from '../constants/unified';

export function useSession() {
  const [session, setSession] = useState<SessionResponsePayload | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [standards, setStandards] = useState<StandardRecord[]>(standardLibrary);
  const [isRetryingSession, setIsRetryingSession] = useState<boolean>(false);
  const [retrySuccess, setRetrySuccess] = useState<boolean | null>(null);
  const [retryMessage, setRetryMessage] = useState<string>('');
  const [sessions, setSessions] = useState<SessionResponsePayload[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(false);

  const loadStandards = useCallback(async (grade: string, strand: string) => {
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
  }, []);

  const initSession = useCallback(
    async (defaultGrade: string = 'Grade 3', defaultStrand: string = 'Connect') => {
      try {
        const result = await api.createSession({
          grade_level: defaultGrade,
          strand_code: defaultStrand,
        });

        if (result.ok) {
          setSession(result.data);
          await loadStandards(
            result.data.grade_level ?? defaultGrade,
            result.data.strand_code ?? defaultStrand
          );
          return result.data;
        } else {
          setSessionError(result.message || 'Unable to start a session');
          return null;
        }
      } catch (err: any) {
        console.error('Failed to initialize session', err);
        setSessionError(err.message || 'Unable to start a session');
        return null;
      }
    },
    [loadStandards]
  );

  const retrySession = useCallback(
    async (defaultGrade: string = 'Grade 3', defaultStrand: string = 'Connect') => {
      setIsRetryingSession(true);
      setRetrySuccess(null);
      setRetryMessage('');
      
      try {
        const result = await api.createSession({
          grade_level: defaultGrade,
          strand_code: defaultStrand,
        });

        if (result.ok) {
          setSession(result.data);
          setSessionError(null);
          setRetrySuccess(true);
          setRetryMessage('Session successfully re-established!');
          await loadStandards(
            result.data.grade_level ?? defaultGrade,
            result.data.strand_code ?? defaultStrand
          );
          return result.data;
        } else {
          setSessionError(result.message || 'Unable to retry session');
          setRetrySuccess(false);
          setRetryMessage(result.message || 'Failed to re-establish session. Please try again.');
          return null;
        }
      } catch (err: any) {
        console.error('Failed to retry session', err);
        const errorMessage = err.message || 'Unable to retry session';
        setSessionError(errorMessage);
        setRetrySuccess(false);
        setRetryMessage(errorMessage);
        return null;
      } finally {
        setIsRetryingSession(false);
        // Clear feedback after 3 seconds
        setTimeout(() => {
          setRetrySuccess(null);
          setRetryMessage('');
        }, 3000);
      }
    },
    [loadStandards]
  );

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const result = await api.listSessions();
      if (result.ok) {
        setSessions(result.data);
        return result.data;
      } else {
        console.error('Failed to load sessions:', result.message);
        return [];
      }
    } catch (err: any) {
      console.error('Failed to load sessions', err);
      return [];
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const loadConversation = useCallback(async (sessionId: string) => {
    try {
      const result = await api.getSession(sessionId);
      if (result.ok) {
        setSession(result.data);
        
        // Load standards for the session's grade and strand
        if (result.data.grade_level && result.data.strand_code) {
          await loadStandards(result.data.grade_level, result.data.strand_code);
        }
        
        return result.data;
      } else {
        console.error('Failed to load conversation:', result.message);
        return null;
      }
    } catch (err: any) {
      console.error('Failed to load conversation', err);
      return null;
    }
  }, [loadStandards]);

  // Format sessions into conversation groups for the sidebar
  const formatSessionsAsConversations = useCallback((): ConversationGroup[] => {
    const now = new Date();
    const today = now.toDateString();
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    const todaySessions: ConversationItem[] = [];
    const thisWeekSessions: ConversationItem[] = [];
    const olderSessions: ConversationItem[] = [];

    sessions.forEach((sessionItem) => {
      const createdDate = new Date(sessionItem.created_at || '');
      const updatedDate = new Date(sessionItem.updated_at || '');
      
      // Count messages from conversation history if available
      let messageCount = 0;
      if (sessionItem.conversation_history) {
        try {
          const history = JSON.parse(sessionItem.conversation_history);
          messageCount = history.length;
        } catch (e) {
          // If parsing fails, just show default
        }
      }
      
      const conversationItem: ConversationItem = {
        id: sessionItem.id,
        title: sessionItem.grade_level
          ? `${sessionItem.grade_level} · ${sessionItem.strand_code || 'Unknown'} Strand`
          : 'Unknown Session',
        hint: formatTimeAgo(updatedDate, messageCount),
        active: session?.id === sessionItem.id,
        grade: sessionItem.grade_level || undefined,
        strand: sessionItem.strand_code || undefined,
        standard: sessionItem.selected_standard?.code,
        createdAt: sessionItem.created_at || undefined,
        updatedAt: sessionItem.updated_at || undefined,
      };

      if (createdDate.toDateString() === today) {
        todaySessions.push(conversationItem);
      } else if (createdDate >= oneWeekAgo) {
        thisWeekSessions.push(conversationItem);
      } else {
        olderSessions.push(conversationItem);
      }
    });

    const groups: ConversationGroup[] = [];
    
    if (todaySessions.length > 0) {
      groups.push({ label: 'Today', items: todaySessions });
    }
    
    if (thisWeekSessions.length > 0) {
      groups.push({ label: 'This Week', items: thisWeekSessions });
    }
    
    if (olderSessions.length > 0) {
      groups.push({ label: 'Older', items: olderSessions });
    }

    return groups;
  }, [sessions, session]);

  // Helper function to format time ago
  const formatTimeAgo = (date: Date, messageCount: number): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      return 'Just now';
    } else if (diffHours < 24) {
      return `${diffHours} hours ago · ${messageCount} messages`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago · ${messageCount} messages`;
    } else {
      return date.toLocaleDateString();
    }
  };

  useEffect(() => {
    initSession();
    loadSessions();
  }, [initSession, loadSessions]);

  return {
    session,
    sessionError,
    standards,
    setSession,
    setStandards,
    initSession,
    loadStandards,
    retrySession,
    isRetryingSession,
    retrySuccess,
    retryMessage,
    sessions,
    isLoadingSessions,
    loadSessions,
    loadConversation,
    formatSessionsAsConversations,
  };
}
