const STORAGE_KEYS = {
  CURRENT_SESSION_ID: "chatbot_current_session_id",
} as const;

export function saveCurrentSessionId(sessionId: string): void {
  try {
    localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION_ID, sessionId);
  } catch (error) {
    console.warn("Failed to save session ID to localStorage:", error);
  }
}

export function getCurrentSessionId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION_ID);
  } catch (error) {
    console.warn("Failed to retrieve session ID from localStorage:", error);
    return null;
  }
}

export function clearCurrentSessionId(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION_ID);
  } catch (error) {
    console.warn("Failed to clear session ID from localStorage:", error);
  }
}

export function isStorageAvailable(): boolean {
  try {
    const test = "__storage_test__";
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
}

// 下位互換性のためのオブジェクト形式での export
export const SessionStorage = {
  saveCurrentSessionId,
  getCurrentSessionId,
  clearCurrentSessionId,
  isStorageAvailable,
};
