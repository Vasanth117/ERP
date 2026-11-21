"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  autoAllocateBatchSections,
  confirmBatchSectionAllocation,
  fetchBatchSectionAllocationPage,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  BatchSectionAllocationPageQuery,
  BatchSectionAllocationRulesPayload,
} from "@/features/college-admin/types/batch-section-allocation";

export function useBatchSectionAllocationPage(params: BatchSectionAllocationPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.batchSectionAllocationPage(params),
    queryFn: () => fetchBatchSectionAllocationPage(params),
  });
}

export function useAutoAllocateBatchSections() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ section_page, unallocated_page }: BatchSectionAllocationPageQuery) =>
      autoAllocateBatchSections(section_page, unallocated_page),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "batch-section-allocation-page"] });
    },
  });
}

export function useConfirmBatchSectionAllocation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: BatchSectionAllocationRulesPayload) => confirmBatchSectionAllocation(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "batch-section-allocation-page"] });
    },
  });
}