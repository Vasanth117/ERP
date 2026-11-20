"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchUserDetailsPage } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useUserDetailsPage(userId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.userDetailsPage(userId ?? ""),
    queryFn: () => fetchUserDetailsPage(userId!),
    enabled: Boolean(userId && userId.length > 10),
  });
}