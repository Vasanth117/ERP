"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { fetchCurrentUser } from "@/features/auth/api";
import { authQueryKeys } from "@/features/auth/query-keys";
import { SESSION_RESTORED_EVENT } from "@/lib/auth/session-ready";
import { getAccessToken } from "@/lib/auth/token-store";

export function useCurrentUser(enabled = true) {
  const queryClient = useQueryClient();
  const [sessionChecked, setSessionChecked] = useState(() =>
    Boolean(getAccessToken()),
  );

  useEffect(() => {
    if (getAccessToken()) {
      setSessionChecked(true);
    }
    const onRestored = () => {
      setSessionChecked(true);
      if (getAccessToken()) {
        void queryClient.invalidateQueries({ queryKey: authQueryKeys.me() });
      }
    };
    window.addEventListener(SESSION_RESTORED_EVENT, onRestored);
    return () => window.removeEventListener(SESSION_RESTORED_EVENT, onRestored);
  }, [queryClient]);

  return useQuery({
    queryKey: authQueryKeys.me(),
    queryFn: fetchCurrentUser,
    enabled: enabled && sessionChecked && Boolean(getAccessToken()),
    staleTime: 60_000,
  });
}