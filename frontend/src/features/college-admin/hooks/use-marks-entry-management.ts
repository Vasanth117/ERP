"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchMarksEntryManagementPage,
  lockMarksEntry,
  sendMarksEntryReminders,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { MarksEntryManagementPageQuery } from "@/features/college-admin/types/marks-entry-management";

export function useMarksEntryManagementPage(params: MarksEntryManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.marksEntryManagementPage(params),
    queryFn: () => fetchMarksEntryManagementPage(params),
  });
}

export function useSendMarksEntryReminders() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: sendMarksEntryReminders,
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.marksEntryManagementPage({ page: variables.page, session_id: variables.session_id }), data);
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}

export function useLockMarksEntry() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: lockMarksEntry,
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.marksEntryManagementPage({ page: variables.page, session_id: variables.session_id }), data);
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}