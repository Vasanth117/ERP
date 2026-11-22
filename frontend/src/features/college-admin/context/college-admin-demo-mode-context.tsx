"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import {
  COLLEGE_ADMIN_DEMO_MODE_EVENT,
  hydrateCollegeAdminDemoViewSession,
  readCollegeAdminDemoModePreference,
  writeCollegeAdminDemoModePreference,
} from "@/lib/demo-mode/college-admin-demo-mode";

type CollegeAdminDemoModeContextValue = {
  /** True when demo view is on (after client hydration reads localStorage). */
  demoMode: boolean;
  /** False during SSR/first paint so server and client markup match. */
  isHydrated: boolean;
  setDemoMode: (enabled: boolean) => void;
};

const CollegeAdminDemoModeContext = createContext<CollegeAdminDemoModeContextValue | null>(
  null,
);

function invalidateCollegeAdminData(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.resetQueries({ queryKey: collegeAdminQueryKeys.all });
  void queryClient.resetQueries({ queryKey: ["ca"] });
  void queryClient.resetQueries({ queryKey: ["college-admin-module"] });
}

export function CollegeAdminDemoModeProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [demoMode, setDemoModeState] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const initial = readCollegeAdminDemoModePreference();
    hydrateCollegeAdminDemoViewSession();
    setDemoModeState(initial);
    setHydrated(true);
    if (initial) {
      invalidateCollegeAdminData(queryClient);
    }
  }, [queryClient]);

  useEffect(() => {
    if (!hydrated) return;
    const onExternal = (event: Event) => {
      const enabled = Boolean((event as CustomEvent<boolean>).detail);
      setDemoModeState(enabled);
    };
    window.addEventListener(COLLEGE_ADMIN_DEMO_MODE_EVENT, onExternal);
    return () => window.removeEventListener(COLLEGE_ADMIN_DEMO_MODE_EVENT, onExternal);
  }, [hydrated]);

  const setDemoMode = useCallback(
    (enabled: boolean) => {
      setDemoModeState(enabled);
      writeCollegeAdminDemoModePreference(enabled);
      invalidateCollegeAdminData(queryClient);
    },
    [queryClient],
  );

  const value = useMemo(
    () => ({
      demoMode: hydrated ? demoMode : false,
      isHydrated: hydrated,
      setDemoMode,
    }),
    [demoMode, hydrated, setDemoMode],
  );

  return (
    <CollegeAdminDemoModeContext.Provider value={value}>
      {children}
    </CollegeAdminDemoModeContext.Provider>
  );
}

export function useCollegeAdminDemoMode(): CollegeAdminDemoModeContextValue {
  const ctx = useContext(CollegeAdminDemoModeContext);
  if (ctx == null) {
    throw new Error("useCollegeAdminDemoMode must be used within CollegeAdminDemoModeProvider");
  }
  return ctx;
}