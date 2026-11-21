"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchFacultyWorkloadManagementPage,
  rebalanceFacultyWorkload,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultyWorkloadManagementQuery } from "@/features/college-admin/types/faculty-workload-management";

export function useFacultyWorkloadManagementPage(params?: FacultyWorkloadManagementQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultyWorkloadManagementPage(params),
    queryFn: () => fetchFacultyWorkloadManagementPage(params),
  });
}

export function useRebalanceFacultyWorkload() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: rebalanceFacultyWorkload,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.facultyWorkloadManagementPage({
          page: 1,
          academic_year_label: variables.academic_year_label ?? data.selected_academic_year,
          semester_label: variables.semester_label ?? data.selected_semester_label,
        }),
        data,
      );
    },
  });
}