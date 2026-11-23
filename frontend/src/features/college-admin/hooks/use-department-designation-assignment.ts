"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchDepartmentDesignationAssignmentPage,
  saveDepartmentDesignationAssignment,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useDepartmentDesignationAssignmentPage(recordId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.departmentDesignationAssignmentPage(recordId),
    queryFn: () => fetchDepartmentDesignationAssignmentPage(recordId),
  });
}

export function useSaveDepartmentDesignationAssignment(recordId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) =>
      saveDepartmentDesignationAssignment({ record_id: recordId, values }),
    onSuccess: (data) => {
      const cacheId = data.form.record_id || recordId;
      void client.setQueryData(collegeAdminQueryKeys.departmentDesignationAssignmentPage(cacheId), data);
    },
  });
}