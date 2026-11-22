"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFacultyAttendanceOverviewPage } from "@/features/college-admin/api/faculty-attendance-overview";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyAttendanceOverviewQuery } from "@/features/college-admin/types/faculty-attendance-overview";

export function useFacultyAttendanceOverviewPage(params?: FacultyAttendanceOverviewQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyAttendanceOverview(params),
    queryFn: () => fetchFacultyAttendanceOverviewPage(params),
  });
}