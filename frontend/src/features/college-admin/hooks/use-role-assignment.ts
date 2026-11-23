"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchRoleAssignmentPage, submitRoleAssignment } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { RoleAssignmentFormValues } from "@/features/college-admin/types/role-assignment";

export function useRoleAssignmentPage(userId: string | null, roleId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.roleAssignmentPage(userId, roleId),
    queryFn: () => fetchRoleAssignmentPage(userId, roleId),
  });
}

export function useSubmitRoleAssignment(userId: string | null, roleId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: RoleAssignmentFormValues) => submitRoleAssignment(form),
    onSuccess: (result) => {
      qc.setQueryData(
        collegeAdminQueryKeys.roleAssignmentPage(userId, roleId),
        result.page,
      );
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.roleManagementDashboard() });
    },
  });
}