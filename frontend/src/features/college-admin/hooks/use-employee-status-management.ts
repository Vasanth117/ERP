"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  approveEmployeeStatusChange,
  fetchEmployeeStatusManagementPage,
  submitEmployeeStatusChange,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { EmployeeStatusManagementPageQuery } from "@/features/college-admin/types/employee-status-management";

export function useEmployeeStatusManagementPage(params: EmployeeStatusManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.employeeStatusManagementPage(params),
    queryFn: () => fetchEmployeeStatusManagementPage(params),
  });
}

export function useSubmitEmployeeStatusChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: submitEmployeeStatusChange,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.employeeStatusManagementPage({
          page: variables.page ?? 1,
          selected_request_id: data.selected_request_id ?? undefined,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.facultyEmployeeHistoryPage() });
    },
  });
}

export function useApproveEmployeeStatusChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: approveEmployeeStatusChange,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.employeeStatusManagementPage({
          page: variables.page ?? 1,
          selected_request_id: data.selected_request_id ?? undefined,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.facultyEmployeeHistoryPage() });
    },
  });
}