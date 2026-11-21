export const SESSION_RESTORED_EVENT = "erp:session-restored";

export function notifySessionRestored(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(SESSION_RESTORED_EVENT));
  }
}