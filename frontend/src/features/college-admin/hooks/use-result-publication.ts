"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchResultPublicationPage,
  publishResultsNow,
  scheduleResultPublication,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ResultPublicationPageQuery } from "@/features/college-admin/types/result-publication";

export function useResultPublicationPage(params: ResultPublicationPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.resultPublicationPage(params),
    queryFn: () => fetchResultPublicationPage(params),
  });
}

export function usePublishResultsNow() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: publishResultsNow,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.resultPublicationPage({ page: variables.page, session_id: variables.session_id }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}

export function useScheduleResultPublication() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: scheduleResultPublication,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.resultPublicationPage({ page: variables.page, session_id: variables.session_id }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}