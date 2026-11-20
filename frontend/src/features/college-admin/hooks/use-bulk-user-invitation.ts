"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchBulkUserInvitationPage,
  sendBulkUserInvitations,
  updateBulkUserInvitationSettings,
  uploadBulkUserInvitation,
} from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useBulkUserInvitationPage(page = 1) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.bulkUserInvitationPage(page),
    queryFn: () => fetchBulkUserInvitationPage(page),
  });
}

export function useUploadBulkUserInvitation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: uploadBulkUserInvitation,
    onSuccess: (data) => {
      qc.setQueryData(collegeAdminQueryKeys.bulkUserInvitationPage(1), data);
    },
  });
}

export function useBulkUserInvitationSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: updateBulkUserInvitationSettings,
    onSuccess: (data) => {
      qc.setQueryData(collegeAdminQueryKeys.bulkUserInvitationPage(data.pagination.page), data);
    },
  });
}

export function useSendBulkUserInvitations() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: sendBulkUserInvitations,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}