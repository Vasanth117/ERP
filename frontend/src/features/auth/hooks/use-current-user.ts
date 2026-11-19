"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchCurrentUser } from "@/features/auth/api";
import { authQueryKeys } from "@/features/auth/query-keys";

export function useCurrentUser(enabled = true) {
  return useQuery({
    queryKey: authQueryKeys.me(),
    queryFn: fetchCurrentUser,
    enabled,
    staleTime: 60_000,
  });
}