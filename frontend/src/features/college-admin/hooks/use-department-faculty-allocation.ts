"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchDepartmentFacultyAllocationPage,
  saveDepartmentFacultyAllocation,
} from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { DepartmentFacultyAllocationFormValues } from "@/features/college-admin/types/department-faculty-allocation";

export function useDepartmentFacultyAllocationPage(params?: {
  page?: number;
  semester_label?: string;
  department_id?: string;
  designation_filter?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentFacultyAllocationPage(params),
    queryFn: () => fetchDepartmentFacultyAllocationPage(params),
  });
}

export function useSaveDepartmentFacultyAllocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { form: DepartmentFacultyAllocationFormValues }) =>
      saveDepartmentFacultyAllocation(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}