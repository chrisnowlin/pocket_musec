/**
 * Utilities for converting between frontend and backend grade formats
 */

/**
 * Convert frontend grade format ("Grade 3", "Kindergarten") to backend format ("3", "K")
 * Note: Kindergarten is stored as "K" in the database (not "0")
 */
export function frontendToBackendGrade(frontendGrade: string): string {
  if (frontendGrade === 'Kindergarten') {
    return 'K';
  }
  
  // Extract number from "Grade X" format
  const match = frontendGrade.match(/Grade (\d+)/);
  if (match) {
    return match[1];
  }
  
  // Return as-is if already in backend format
  return frontendGrade;
}

/**
 * Convert backend grade format ("3", "K") to frontend format ("Grade 3", "Kindergarten")
 * Note: "K" in the database represents Kindergarten
 */
export function backendToFrontendGrade(backendGrade: string): string {
  if (backendGrade === 'K' || backendGrade === '0') {
    // Handle both "K" (database format) and "0" (legacy format) for backward compatibility
    return 'Kindergarten';
  }
  
  if (backendGrade === 'AC') {
    return 'Accomplished';
  }
  
  if (backendGrade === 'AD') {
    return 'Advanced';
  }
  
  // If it's a number, add "Grade" prefix
  if (/^\d+$/.test(backendGrade)) {
    return `Grade ${backendGrade}`;
  }
  
  // Return as-is if unknown format
  return backendGrade;
}

/**
 * Convert frontend strand name ("Connect") to backend strand code ("CONNECT")
 */
export function frontendToBackendStrand(frontendStrand: string): string {
  const mapping: Record<string, string> = {
    'Connect': 'CONNECT',
    'Create': 'CREATE',
    'Present': 'PRESENT',
    'Respond': 'RESPOND',
  };

  return mapping[frontendStrand] || frontendStrand;
}

/**
 * Convert backend strand code ("CONNECT") to frontend strand name ("Connect")
 */
export function backendToFrontendStrand(backendStrand: string): string {
  const mapping: Record<string, string> = {
    'CONNECT': 'Connect',
    'CREATE': 'Create',
    'PRESENT': 'Present',
    'RESPOND': 'Respond',
  };

  return mapping[backendStrand] || backendStrand;
}
