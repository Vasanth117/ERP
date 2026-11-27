"use client";

import { useMemo } from "react";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import {
  fetchCommunicationScheduledMessagesPage,
  fetchCommunicationTemplatesManagementPage,
} from "@/features/college-admin/api/communication-templates-scheduling";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCommunicationTemplatesManagementPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationTemplatesManagementPage(params),
    queryFn: () => fetchCommunicationTemplatesManagementPage(params),
    enabled,
  });
}

export function useCommunicationScheduledMessagesPage(
  params?: { page?: number; page_size?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.communicationScheduledMessagesPage(params),
    queryFn: () => fetchCommunicationScheduledMessagesPage(params),
    enabled,
  });
}

export function useCommunicationTemplatesSchedulingPage(
  variant: "templates" | "scheduled",
  page: number,
  pageSize: number,
) {
  const params = useMemo(() => ({ page, page_size: pageSize }), [page, pageSize]);
  const templates = useCommunicationTemplatesManagementPage(params, variant === "templates");
  const scheduled = useCommunicationScheduledMessagesPage(params, variant === "scheduled");
  return variant === "scheduled" ? scheduled : templates;
}