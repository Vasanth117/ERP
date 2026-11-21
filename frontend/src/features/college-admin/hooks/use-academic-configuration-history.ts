"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAcademicConfigurationHistoryPage } from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAcademicConfigurationHistoryPage(params: {
  page?: number;
  date_range?: string;
  setting_area?: string;
  actor_id?: string;
  search?: string;
  selected_change_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicConfigurationHistoryPage(params),
    queryFn: () => fetchAcademicConfigurationHistoryPage(params),
  });
}