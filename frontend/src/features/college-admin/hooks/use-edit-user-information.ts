"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchEditUserInformationPage, saveEditUserInformation } from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useEditUserInformationPage(userId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.editUserInformationPage(userId ?? ""),
    queryFn: () => fetchEditUserInformationPage(userId!),
    enabled: Boolean(userId && userId.length > 10),
  });
}

export function useSaveEditUserInformation(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) => saveEditUserInformation({ user_id: userId, values }),
    onSuccess: (data) => {
      qc.setQueryData(collegeAdminQueryKeys.editUserInformationPage(userId), data);
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.userDetailsPage(userId) });
    },
  });
}