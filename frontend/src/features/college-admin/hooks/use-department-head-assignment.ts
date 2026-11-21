"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchDepartmentHeadAssignmentPage,
  submitDepartmentHeadAssignment,
} from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { DepartmentHeadAssignmentFormValues } from "@/features/college-admin/types/department-head-assignment";

export function useDepartmentHeadAssignmentPage(params?: {
  page?: number;
  selected_department_id?: string;
  faculty_user_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentHeadAssignmentPage(params),
    queryFn: () => fetchDepartmentHeadAssignmentPage(params),
  });
}

export function useSubmitDepartmentHeadAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { department_id: string; form: DepartmentHeadAssignmentFormValues }) =>
      submitDepartmentHeadAssignment(payload),
    onSuccess: (result) => {
      void queryClient.setQueryData(
        collegeAdminQueryKeys.departmentHeadAssignmentPage({
          page: result.page.pagination.page,
          selected_department_id: result.page.selected_department_id ?? undefined,
          faculty_user_id: result.page.form.faculty_user_id || undefined,
        }),
        result.page,
      );
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}