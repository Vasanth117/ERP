"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addBatchSection,
  autoAllocateBatchSections,
  fetchBatchSectionConfigurationPage,
  saveBatchSectionAllocationRules,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  BatchSectionAddSectionPayload,
  BatchSectionAllocationRulesPayload,
  BatchSectionAutoAllocatePayload,
} from "@/features/college-admin/types/batch-section-configuration";

export type BatchSectionPageParams = {
  batch_year?: string;
  programme_code?: string;
  page?: number;
};

export function useBatchSectionConfigurationPage(params?: BatchSectionPageParams) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.batchSectionConfiguration(params),
    queryFn: () => fetchBatchSectionConfigurationPage(params),
  });
}

export function useSaveBatchSectionRules() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BatchSectionAllocationRulesPayload) => saveBatchSectionAllocationRules(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.batchSectionConfiguration() });
    },
  });
}

export function useAddBatchSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BatchSectionAddSectionPayload) => addBatchSection(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.batchSectionConfiguration() });
    },
  });
}

export function useAutoAllocateBatchSections() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BatchSectionAutoAllocatePayload) => autoAllocateBatchSections(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.batchSectionConfiguration() });
    },
  });
}