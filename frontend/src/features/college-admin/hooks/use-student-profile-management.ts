"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchStudentProfileManagementPage,
  saveStudentProfileManagement,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentProfileManagementPage(recordId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentProfileManagementPage(recordId),
    queryFn: () => fetchStudentProfileManagementPage(recordId),
  });
}

export function useSaveStudentProfileManagement(recordId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) =>
      saveStudentProfileManagement({ record_id: recordId, values }),
    onSuccess: (data) => {
      void client.setQueryData(collegeAdminQueryKeys.studentProfileManagementPage(recordId), data);
    },
  });
}