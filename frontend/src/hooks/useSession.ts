import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { SessionResponsePayload, StandardRecord } from '../lib/types';
import type { ConversationGroup, ConversationItem } from '../types/unified';
import { frontendToBackendGrade, frontendToBackendStrand } from '../lib/gradeUtils';

// Helper function to transform API response from snake_case to camelCase
const transformStandard = (standard: any): StandardRecord => {
  return {
    ...standard,
    learningObjectives: standard.learning_objectives || standard.learningObjectives || [],
  };
};

// Helper function to transform session's selected_standard if present
const transformSession = (session: any): SessionResponsePayload => {
  if (session.selected_standard) {
    session.selected_standard = transformStandard(session.selected_standard);
  }
  return session;
};

export function useSession() {
  const [session, setSession] = useState<SessionResponsePayload | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [standards, setStandards] = useState<StandardRecord[]>([]);
  const [isRetryingSession, setIsRetryingSession] = useState<boolean>(false);
  const [retrySuccess, setRetrySuccess] = useState<boolean | null>(null);
  const [retryMessage, setRetryMessage] = useState<string>('');
  const [sessions, setSessions] = useState<SessionResponsePayload[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(false);

  const loadStandards = useCallback(async (grade: string, strand: string) => {
    try {
      // Handle "All Grades" and "All Strands" - don't filter by these
      const params: { grade_level?: string; strand_code?: string } = {};
      
      if (grade && grade !== 'All Grades') {
        params.grade_level = frontendToBackendGrade(grade);
      }
      
      if (strand && strand !== 'All Strands') {
        params.strand_code = frontendToBackendStrand(strand);
      }
      
      const result = await api.listStandards(params);

      if (result.ok) {
        // Transform API response from snake_case to camelCase
        const payload = result.data.map(transformStandard);
        setStandards(payload);
      }
    } catch (err) {
      console.error('Failed to load standards', err);
    }
  }, []);

  const initSession = useCallback(
    async (
      defaultGrade: string = 'Grade 3',
      defaultStrand: string = 'Connect',
      standardId?: string | null,
      additionalContext?: string | null
    ) => {
      try {
        const payload: any = {
          grade_level: defaultGrade,
          strand_code: defaultStrand,
        };
        
        if (standardId) {
          payload.standard_id = standardId;
        }
        
        if (additionalContext) {
          payload.additional_context = additionalContext;
        }
        
        const result = await api.createSession(payload);

        if (result.ok) {
          const transformedSession = transformSession(result.data);
          setSession(transformedSession);
          await loadStandards(
            transformedSession.grade_level ?? defaultGrade,
            transformedSession.strand_code ?? defaultStrand
          );
          return transformedSession;
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
          const transformedSession = transformSession(result.data);
          setSession(transformedSession);
          setSessionError(null);
          setRetrySuccess(true);
          setRetryMessage('Session successfully re-established!');
          await loadStandards(
            transformedSession.grade_level ?? defaultGrade,
            transformedSession.strand_code ?? defaultStrand
          );
          return transformedSession;
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
        // Transform selected_standard if present
        const transformedSession = transformSession(result.data);
        setSession(transformedSession);
        
        // Load standards for the session's grade and strand
        if (transformedSession.grade_level && transformedSession.strand_code) {
          await loadStandards(transformedSession.grade_level, transformedSession.strand_code);
        }
        
        return transformedSession;
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
      // Parse dates with validation - use created_at as fallback if updated_at is invalid
      let updatedDate = sessionItem.updated_at ? new Date(sessionItem.updated_at) : null;
      if (!updatedDate || isNaN(updatedDate.getTime())) {
        // If updated_at is invalid, try created_at
        updatedDate = sessionItem.created_at ? new Date(sessionItem.created_at) : new Date();
        // If still invalid, use current time
        if (!updatedDate || isNaN(updatedDate.getTime())) {
          updatedDate = new Date();
        }
      }
      
      let createdDate = sessionItem.created_at ? new Date(sessionItem.created_at) : updatedDate;
      if (!createdDate || isNaN(createdDate.getTime())) {
        // Fallback to current date if created_at is also invalid
        createdDate = new Date();
      }
      
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

    // Combine today and this week sessions for "Recent Chats"
    // Sort all recent sessions by most recently updated and limit to 3
    const allRecentSessions = [...todaySessions, ...thisWeekSessions]
      .sort((a, b) => {
        const dateA = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
        const dateB = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
        return dateB - dateA; // Most recent first
      })
      .slice(0, 3); // Limit to 3 most recent

    const groups: ConversationGroup[] = [];
    
    // Show "Recent Chats" if there are any sessions from this week (including today)
    if (allRecentSessions.length > 0) {
      groups.push({ label: 'Recent Chats', items: allRecentSessions });
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
    
    // Handle invalid dates or future dates
    if (isNaN(diffMs) || diffMs < 0) {
      return messageCount > 0 ? `${messageCount} messages` : 'Unknown time';
    }
    
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) {
      return messageCount > 0 ? `Just now · ${messageCount} messages` : 'Just now';
    } else if (diffMinutes < 60) {
      return messageCount > 0 
        ? `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago · ${messageCount} messages`
        : `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return messageCount > 0 
        ? `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago · ${messageCount} messages`
        : `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays === 1) {
      return messageCount > 0 ? `Yesterday · ${messageCount} messages` : 'Yesterday';
    } else if (diffDays < 7) {
      return messageCount > 0 
        ? `${diffDays} days ago · ${messageCount} messages`
        : `${diffDays} days ago`;
    } else {
      return messageCount > 0 
        ? `${date.toLocaleDateString()} · ${messageCount} messages`
        : date.toLocaleDateString();
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
    setSessions,
    isLoadingSessions,
    loadSessions,
    loadConversation,
    formatSessionsAsConversations,
  };
}
