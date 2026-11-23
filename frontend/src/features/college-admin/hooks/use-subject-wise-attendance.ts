"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchSubjectWiseAttendancePage } from "@/features/college-admin/api/subject-wise-attendance";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { SubjectWiseAttendanceQuery } from "@/features/college-admin/types/subject-wise-attendance";

export function useSubjectWiseAttendancePage(params?: SubjectWiseAttendanceQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.subjectWiseAttendance(params),
    queryFn: () => fetchSubjectWiseAttendancePage(params),
  });
}