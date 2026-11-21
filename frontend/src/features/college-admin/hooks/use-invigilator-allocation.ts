"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  autoAssignInvigilators,
  fetchInvigilatorAllocationPage,
  publishInvigilatorRoster,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { InvigilatorAllocationPageQuery } from "@/features/college-admin/types/invigilator-allocation";

export function useInvigilatorAllocationPage(params: InvigilatorAllocationPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.invigilatorAllocationPage(params),
    queryFn: () => fetchInvigilatorAllocationPage(params),
  });
}

export function useAutoAssignInvigilators() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: autoAssignInvigilators,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.invigilatorAllocationPage({
          page: variables.page,
          session_id: variables.session_id,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}

export function usePublishInvigilatorRoster() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: publishInvigilatorRoster,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.invigilatorAllocationPage({
          page: variables.page,
          session_id: variables.session_id,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}