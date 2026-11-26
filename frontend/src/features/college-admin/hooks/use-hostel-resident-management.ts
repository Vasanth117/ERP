"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelResidentManagementPage } from "@/features/college-admin/api/hostel-resident-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelResidentManagementPageQuery } from "@/features/college-admin/types/hostel-resident-management";

export function useHostelResidentManagementPage(params?: HostelResidentManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelResidentManagementPage(params),
    queryFn: () => fetchHostelResidentManagementPage(params),
  });
}