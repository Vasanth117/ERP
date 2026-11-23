"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchEmployeeProfileManagementPage,
  saveEmployeeProfileManagement,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useEmployeeProfileManagementPage(recordId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.employeeProfileManagementPage(recordId),
    queryFn: () => fetchEmployeeProfileManagementPage(recordId),
  });
}

export function useSaveEmployeeProfileManagement(recordId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) =>
      saveEmployeeProfileManagement({ record_id: recordId, values }),
    onSuccess: (data) => {
      const cacheId = data.record_id ?? recordId;
      void client.setQueryData(collegeAdminQueryKeys.employeeProfileManagementPage(cacheId), data);
    },
  });
}