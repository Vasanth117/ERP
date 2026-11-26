"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelBuildingManagementPage } from "@/features/college-admin/api/hostel-building-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelBuildingManagementPageQuery } from "@/features/college-admin/types/hostel-building-management";

export function useHostelBuildingManagementPage(params?: HostelBuildingManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelBuildingManagementPage(params),
    queryFn: () => fetchHostelBuildingManagementPage(params),
  });
}