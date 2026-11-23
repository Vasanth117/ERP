"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchCreateEditRolePage, saveCreateEditRole } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  CreateEditRoleFormValues,
  CreateEditRolePermissionToggle,
} from "@/features/college-admin/types/create-edit-role";

export function useCreateEditRolePage(roleId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.createEditRolePage(roleId),
    queryFn: () => fetchCreateEditRolePage(roleId),
  });
}

export function useSaveCreateEditRole(roleId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      form: CreateEditRoleFormValues;
      permission_toggles: CreateEditRolePermissionToggle[];
    }) =>
      saveCreateEditRole({
        role_id: roleId,
        form: payload.form,
        permission_toggles: payload.permission_toggles,
      }),
    onSuccess: (data) => {
      qc.setQueryData(collegeAdminQueryKeys.createEditRolePage(roleId), data);
      if (data.role_id) {
        qc.setQueryData(collegeAdminQueryKeys.createEditRolePage(data.role_id), data);
      }
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.roleManagementDashboard() });
    },
  });
}