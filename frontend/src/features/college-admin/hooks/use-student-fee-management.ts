"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchStudentFeeManagementPage } from "@/features/college-admin/api/student-fee-management";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentFeeManagementPageQuery } from "@/features/college-admin/types/student-fee-management";

export function useStudentFeeManagementPage(params: StudentFeeManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentFeeManagementPage(params),
    queryFn: () => fetchStudentFeeManagementPage(params),
  });
}