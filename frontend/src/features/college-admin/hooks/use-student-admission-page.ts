"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchStudentAdmissionPage } from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentAdmissionPageQuery } from "@/features/college-admin/types/student-admission";

export function useStudentAdmissionPage(params: StudentAdmissionPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentAdmissionPage(params),
    queryFn: () => fetchStudentAdmissionPage(params),
  });
}