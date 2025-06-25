const STORAGE_KEYS = {
  CURRENT_SESSION_ID: 'chatbot_current_session_id',
} as const;

export class SessionStorage {
  static saveCurrentSessionId(sessionId: string): void {
    try {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION_ID, sessionId);
    } catch (error) {
      console.warn('Failed to save session ID to localStorage:', error);
    }
  }

  static getCurrentSessionId(): string | null {
    try {
      return localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION_ID);
    } catch (error) {
      console.warn('Failed to retrieve session ID from localStorage:', error);
      return null;
    }
  }

  static clearCurrentSessionId(): void {
    try {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION_ID);
    } catch (error) {
      console.warn('Failed to clear session ID from localStorage:', error);
    }
  }

  static isStorageAvailable(): boolean {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }
}