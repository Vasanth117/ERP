"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchStudentAcademicHistoryPage } from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentAcademicHistoryPage(recordId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentAcademicHistoryPage(recordId ?? ""),
    queryFn: () => fetchStudentAcademicHistoryPage(recordId!),
    enabled: Boolean(recordId),
  });
}