"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchAttendanceSectionSubNav } from "@/features/college-admin/api/attendance-section-sub-nav";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useAttendanceSectionSubNav(path: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.attendanceSectionSubNav(path),
    queryFn: () => fetchAttendanceSectionSubNav(path),
    enabled: Boolean(path),
  });
}