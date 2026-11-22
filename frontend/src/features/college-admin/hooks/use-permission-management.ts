"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  downloadPermissionManagementMatrix,
  fetchPermissionManagementPage,
  savePermissionManagementMatrix,
} from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { PermissionManagementMatrixChange } from "@/features/college-admin/types/permission-management";

export function usePermissionManagementPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.permissionManagementPage(),
    queryFn: () => fetchPermissionManagementPage(),
  });
}

export function useSavePermissionManagementMatrix() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (changes: PermissionManagementMatrixChange[]) =>
      savePermissionManagementMatrix({ changes }),
    onSuccess: (data) => {
      qc.setQueryData(collegeAdminQueryKeys.permissionManagementPage(), data);
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.roleManagementDashboard() });
    },
  });
}

export function useDownloadPermissionMatrix() {
  return useMutation({
    mutationFn: () => downloadPermissionManagementMatrix(),
  });
}