"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import {
  downloadLoginAccountActivityExport,
  fetchLoginAccountActivityPage,
} from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useLoginAccountActivityPage(params: {
  date_range?: string;
  role_filter?: string;
  location_filter?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.loginAccountActivityPage(params),
    queryFn: () => fetchLoginAccountActivityPage(params),
  });
}

export function useDownloadLoginAccountActivity(params: {
  date_range?: string;
  role_filter?: string;
  location_filter?: string;
}) {
  return useMutation({
    mutationFn: () => downloadLoginAccountActivityExport(params),
  });
}