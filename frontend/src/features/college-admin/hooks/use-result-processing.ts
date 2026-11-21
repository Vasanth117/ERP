"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchResultProcessingPage, processResults } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ResultProcessingPageQuery } from "@/features/college-admin/types/result-processing";

export function useResultProcessingPage(params: ResultProcessingPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.resultProcessingPage(params),
    queryFn: () => fetchResultProcessingPage(params),
  });
}

export function useProcessResults() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: processResults,
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.resultProcessingPage({ session_id: variables.session_id }), data);
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}