"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  bulkEnrollStudents,
  fetchStudentEnrollmentManagementPage,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { StudentEnrollmentManagementPageQuery } from "@/features/college-admin/types/student-enrollment-management";

export function useStudentEnrollmentManagementPage(params: StudentEnrollmentManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentEnrollmentManagementPage(params),
    queryFn: () => fetchStudentEnrollmentManagementPage(params),
  });
}

export function useBulkEnrollStudents() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: bulkEnrollStudents,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.studentEnrollmentManagementPage({
          page: variables.page,
          term_key: variables.term_key,
          programme_code: variables.programme_code,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}