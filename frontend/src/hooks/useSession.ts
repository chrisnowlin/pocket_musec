import { useState, useCallback, useEffect } from 'react';
import api from '../lib/api';
import type { SessionResponsePayload, StandardRecord } from '../lib/types';
import { standardLibrary } from '../constants/unified';

export function useSession() {
  const [session, setSession] = useState<SessionResponsePayload | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [standards, setStandards] = useState<StandardRecord[]>(standardLibrary);

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

  useEffect(() => {
    initSession();
  }, [initSession]);

  return {
    session,
    sessionError,
    standards,
    setSession,
    setStandards,
    initSession,
    loadStandards,
  };
}
