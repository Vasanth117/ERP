"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchCreateEditDepartmentPage, saveCreateEditDepartment } from "@/features/college-admin/api/organization";
import type { CreateEditDepartmentFormValues } from "@/features/college-admin/types/create-edit-department";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useCreateEditDepartmentPage(departmentId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.createEditDepartmentPage(departmentId),
    queryFn: () => fetchCreateEditDepartmentPage(departmentId),
  });
}

export function useSaveCreateEditDepartment(departmentId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { mode: "create" | "draft"; form: CreateEditDepartmentFormValues }) =>
      saveCreateEditDepartment({
        department_id: departmentId,
        mode: payload.mode,
        form: payload.form,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}