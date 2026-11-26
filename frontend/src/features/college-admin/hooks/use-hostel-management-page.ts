"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelManagementPage } from "@/features/college-admin/api/hostel-management-page";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelManagementPageQuery } from "@/features/college-admin/types/hostel-management-page";

export function useHostelManagementPage(screenSlug: string, params?: HostelManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelManagementPage(screenSlug, params),
    queryFn: () => fetchHostelManagementPage(screenSlug, params),
    enabled: Boolean(screenSlug),
  });
}