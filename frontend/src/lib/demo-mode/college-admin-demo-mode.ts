"use client";

export const COLLEGE_ADMIN_DEMO_MODE_STORAGE_KEY = "college-admin-demo-mode";
export const COLLEGE_ADMIN_DEMO_VIEW_SESSION_KEY = "erp.demo_college_view";
export const COLLEGE_ADMIN_DEMO_MODE_EVENT = "college-admin-demo-mode";

export function readCollegeAdminDemoModePreference(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(COLLEGE_ADMIN_DEMO_MODE_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function writeCollegeAdminDemoModePreference(enabled: boolean): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(COLLEGE_ADMIN_DEMO_MODE_STORAGE_KEY, enabled ? "1" : "0");
  } catch {
    /* ignore */
  }
  syncCollegeAdminDemoViewSession(enabled);
  window.dispatchEvent(
    new CustomEvent(COLLEGE_ADMIN_DEMO_MODE_EVENT, { detail: enabled }),
  );
}

export function syncCollegeAdminDemoViewSession(enabled: boolean): void {
  if (typeof window === "undefined" || typeof sessionStorage === "undefined") {
    return;
  }
  try {
    if (enabled) {
      sessionStorage.setItem(COLLEGE_ADMIN_DEMO_VIEW_SESSION_KEY, "1");
    } else {
      sessionStorage.removeItem(COLLEGE_ADMIN_DEMO_VIEW_SESSION_KEY);
    }
  } catch {
    /* ignore */
  }
}

export function isCollegeAdminDemoViewActive(): boolean {
  if (typeof window === "undefined" || typeof sessionStorage === "undefined") {
    return false;
  }
  try {
    return sessionStorage.getItem(COLLEGE_ADMIN_DEMO_VIEW_SESSION_KEY) === "1";
  } catch {
    return false;
  }
}

/** Call once on college-admin shell mount so API client sees persisted demo preference. */
export function hydrateCollegeAdminDemoViewSession(): void {
  syncCollegeAdminDemoViewSession(readCollegeAdminDemoModePreference());
}