"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchHostelSectionSubNav } from "@/features/college-admin/api/hostel-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useHostelSectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelSectionSubNav(path),
    queryFn: () => fetchHostelSectionSubNav(path),
    enabled: Boolean(path),
  });
}