"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveResultApproval,
  fetchResultApprovalPage,
  returnResultApproval,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ResultApprovalPageQuery } from "@/features/college-admin/types/result-approval";

export function useResultApprovalPage(params: ResultApprovalPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.resultApprovalPage(params),
    queryFn: () => fetchResultApprovalPage(params),
  });
}

export function useApproveResultApproval() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: approveResultApproval,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.resultApprovalPage({ page: variables.page, session_id: variables.session_id }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}

export function useReturnResultApproval() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: returnResultApproval,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.resultApprovalPage({ page: variables.page, session_id: variables.session_id }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}