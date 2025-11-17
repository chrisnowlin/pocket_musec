export interface AuthInfo {
  token?: string;
  userId?: string;
  user_id?: string;
  [key: string]: unknown;
}

function parseAuth(raw: string | null): AuthInfo | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthInfo;
  } catch (error) {
    console.warn('Failed to parse auth payload from storage', error);
    return null;
  }
}

export function getAuth(): AuthInfo | null {
  const stored = localStorage.getItem('auth') || localStorage.getItem('auth_info');
  if (stored) {
    return parseAuth(stored);
  }

  const token = localStorage.getItem('auth_token');
  const userId = localStorage.getItem('user_id');
  if (token || userId) {
    return { token: token || undefined, userId: userId || undefined };
  }

  return null;
}

export function getAuthToken(): string | null {
  const auth = getAuth();
  return (auth?.token as string | undefined) || (auth?.access_token as string | undefined) || localStorage.getItem('auth_token');
}

export function getAuthUserId(): string | null {
  const auth = getAuth();
  return (auth?.userId as string | undefined) || (auth?.user_id as string | undefined) || localStorage.getItem('user_id');
}
