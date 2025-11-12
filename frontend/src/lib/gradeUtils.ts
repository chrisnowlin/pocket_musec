/**
 * Utilities for converting between frontend and backend grade formats
 */

/**
 * Convert frontend grade format ("Grade 3", "Kindergarten") to backend format ("3", "0")
 * Note: Kindergarten is stored as "0" in the database to sort before Grade 1
 */
export function frontendToBackendGrade(frontendGrade: string): string {
  if (frontendGrade === 'Kindergarten') {
    return '0';
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
 * Convert backend grade format ("3", "0") to frontend format ("Grade 3", "Kindergarten")
 * Note: "0" in the database represents Kindergarten for proper sorting
 */
export function backendToFrontendGrade(backendGrade: string): string {
  if (backendGrade === '0' || backendGrade === 'K') {
    // Handle both "0" (new format) and "K" (legacy format) for backward compatibility
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
 * Convert frontend strand name ("Connect") to backend strand code ("CN")
 */
export function frontendToBackendStrand(frontendStrand: string): string {
  const mapping: Record<string, string> = {
    'Connect': 'CN',
    'Create': 'CR',
    'Present': 'PR',
    'Respond': 'RE',
  };
  
  return mapping[frontendStrand] || frontendStrand;
}

/**
 * Convert backend strand code ("CN") to frontend strand name ("Connect")
 */
export function backendToFrontendStrand(backendStrand: string): string {
  const mapping: Record<string, string> = {
    'CN': 'Connect',
    'CR': 'Create',
    'PR': 'Present',
    'RE': 'Respond',
  };
  
  return mapping[backendStrand] || backendStrand;
}
