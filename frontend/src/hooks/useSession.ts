import { useState, useCallback, useEffect, useRef, type SetStateAction } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { SessionResponsePayload, StandardRecord } from '../lib/types';
import type { ConversationGroup, ConversationItem } from '../types/unified';
import { frontendToBackendGrade, frontendToBackendStrand } from '../lib/gradeUtils';
import { useConversationStore } from '../stores/conversationStore';

// Helper function to transform API response from snake_case to camelCase
const transformStandard = (standard: any): StandardRecord => {
  return {
    ...standard,
    learningObjectives: standard.learning_objectives || standard.learningObjectives || [],
  };
};

// Helper function to transform session's selected_standards if present
const transformSession = (session: any): SessionResponsePayload => {
  if (session.selected_standards && Array.isArray(session.selected_standards)) {
    session.selected_standards = session.selected_standards.map(transformStandard);
  }
  // Handle backward compatibility for old single standard format
  else if (session.selected_standard) {
    session.selected_standards = [transformStandard(session.selected_standard)];
    delete session.selected_standard;
  }
  // Handle backward compatibility for old single objectives format
  if (session.selected_objectives && typeof session.selected_objectives === 'string') {
    // Convert comma-separated string to array
    session.selected_objectives = session.selected_objectives.split(',').filter((obj: string) => obj.trim());
  }
  return session;
};

export function useSession() {
  const session = useConversationStore((state) => state.session);
  const setSession = useConversationStore((state) => state.setSession);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [standards, setStandards] = useState<StandardRecord[]>([]);
  const [isRetryingSession, setIsRetryingSession] = useState<boolean>(false);
  const [retrySuccess, setRetrySuccess] = useState<boolean | null>(null);
  const [retryMessage, setRetryMessage] = useState<string>('');
  const queryClient = useQueryClient();
  const {
    data: sessionsData,
    isFetching: isLoadingSessions,
    refetch: refetchSessions,
  } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const result = await api.listSessions();
      if (!result.ok) {
        throw new Error(result.message || 'Failed to load sessions');
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5,
  });
  const sessions = sessionsData ?? [];
  const setSessions = useCallback((updater: SetStateAction<SessionResponsePayload[]>) => {
    queryClient.setQueryData<SessionResponsePayload[]>(['sessions'], (current = []) => {
      if (typeof updater === 'function') {
        return (updater as (prev: SessionResponsePayload[]) => SessionResponsePayload[])(current);
      }
      return updater;
    });
  }, [queryClient]);
  const standardsRequestRef = useRef(0);
  const retryFeedbackTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadStandards = useCallback(async (grade: string, strand: string) => {
    try {
      standardsRequestRef.current += 1;
      const requestId = standardsRequestRef.current;
      // Handle "All Grades" and "All Strands" - don't filter by these
      const params: { grade_level?: string; strand_code?: string; limit?: number } = {};
      
      if (grade && grade !== 'All Grades') {
        params.grade_level = frontendToBackendGrade(grade);
      }
      
      if (strand && strand !== 'All Strands') {
        params.strand_code = frontendToBackendStrand(strand);
      }
      
      // Always request enough standards to include all grades (default limit is 50, but we have 112+ standards)
      params.limit = 200;
      
      const result = await api.listStandards(params);

      if (result.ok && requestId === standardsRequestRef.current) {
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
      additionalContext?: string | null,
      lessonDuration?: number | null,
      classSize?: number | null,
      selectedObjectives?: string[] | null,
      additionalStandards?: StandardRecord[] | null,
      selectedModel?: string | null
    ) => {
      try {
        const payload: any = {
          grade_level: defaultGrade,
          strand_code: defaultStrand,
        };
        
        // Combine primary standard and additional standards into a single array
        const allStandards = additionalStandards || [];
        if (standardId) {
          // For backward compatibility, send as standard_id if single, otherwise as array
          payload.standard_id = standardId;
        }
        
        if (additionalContext) {
          payload.additional_context = additionalContext;
        }
        
        if (selectedObjectives && selectedObjectives.length > 0) {
          payload.selected_objectives = selectedObjectives;
        }
        
        if (additionalStandards && additionalStandards.length > 0) {
          payload.additional_standards = additionalStandards.map(s => s.id);
        }
        
        if (selectedModel) {
          payload.selected_model = selectedModel;
        }
        
        const result = await api.createSession(payload);

        if (result.ok) {
          const transformedSession = transformSession(result.data);
          setSession(transformedSession);
          setSessionError(null);
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
        if (retryFeedbackTimeoutRef.current) {
          clearTimeout(retryFeedbackTimeoutRef.current);
        }
        // Clear feedback after 3 seconds
        retryFeedbackTimeoutRef.current = setTimeout(() => {
          setRetrySuccess(null);
          setRetryMessage('');
        }, 3000);
      }
    },
    [loadStandards]
  );

  const loadSessions = useCallback(async () => {
    const result = await refetchSessions();
    return result.data ?? [];
  }, [refetchSessions]);

  const loadConversation = useCallback(async (sessionId: string) => {
    try {
      const result = await api.getSession(sessionId);
      if (result.ok) {
        // Transform selected_standard if present
        const transformedSession = transformSession(result.data);
        setSession(transformedSession);
        setSessionError(null);
        
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
      // Parse dates with validation - handle ISO format properly
      const parseIsoDate = (dateStr: string): Date => {
        if (!dateStr) return new Date();
        
        // Add Z suffix if missing for proper UTC parsing
        const normalizedDate = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
        const date = new Date(normalizedDate);
        return isNaN(date.getTime()) ? new Date() : date;
      };
      
      let updatedDate = parseIsoDate(sessionItem.updated_at || '');
      if (!sessionItem.updated_at) {
        // If no updated_at, use created_at
        updatedDate = parseIsoDate(sessionItem.created_at || '');
      }
      
      let createdDate = parseIsoDate(sessionItem.created_at || '');
      
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
      
      // Generate a more descriptive title based on available context
      let title = 'New Conversation';
      
      if (sessionItem.grade_level) {
        if (sessionItem.strand_code && sessionItem.strand_code !== 'All Strands') {
          title = `${sessionItem.grade_level} · ${sessionItem.strand_code}`;
        } else {
          title = sessionItem.grade_level;
        }
      }
      
      // Add standard info if available
      if (sessionItem.selected_standards && sessionItem.selected_standards.length > 0) {
        title += ` · ${sessionItem.selected_standards[0].code}`;
      }
      
      // Add context indicator if there's additional context
      if (sessionItem.additional_context && sessionItem.additional_context.trim()) {
        title += ' 📝';
      }
      
      const conversationItem: ConversationItem = {
        id: sessionItem.id,
        title: title,
        hint: formatTimeAgo(updatedDate, messageCount),
        active: session?.id === sessionItem.id,
        grade: sessionItem.grade_level || undefined,
        strand: sessionItem.strand_code || undefined,
        standard: sessionItem.selected_standards?.[0]?.code,
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

  const updateSelectedModel = useCallback(
    async (sessionId: string, selectedModel: string | null, updatedSession?: SessionResponsePayload) => {
      try {
        // If we already have the updated session from the API response, use it directly
        if (updatedSession) {
          const transformedSession = transformSession(updatedSession);
          setSession(transformedSession);
          return transformedSession;
        }

        // Otherwise, make an API call to update and get the session
        const result = await api.updateSession(sessionId, {
          selected_model: selectedModel || undefined,
        });

        if (result.ok) {
          const transformedSession = transformSession(result.data);
          setSession(transformedSession);
          return transformedSession;
        } else {
          console.error('Failed to update model:', result.message);
          return null;
        }
      } catch (err: any) {
        console.error('Failed to update selected model', err);
        return null;
      }
    },
    []
  );

  useEffect(() => {
    return () => {
      if (retryFeedbackTimeoutRef.current) {
        clearTimeout(retryFeedbackTimeoutRef.current);
      }
    };
  }, []);

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
    updateSelectedModel,
  };
}
