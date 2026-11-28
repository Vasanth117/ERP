"use client";

import { useMutation } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import {
  fetchFeeStructureCreationPage,
  publishFeeStructure,
  saveFeeStructure,
} from "@/features/college-admin/api/fee-structure-creation";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FeeStructureUpsertPayload } from "@/features/college-admin/types/fee-structure-creation";

export function useFeeStructureCreationPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.feeStructureCreationPage(),
    queryFn: fetchFeeStructureCreationPage,
  });
}

export function useSaveFeeStructure() {
  return useMutation({ mutationFn: (payload: FeeStructureUpsertPayload) => saveFeeStructure(payload) });
}

export function usePublishFeeStructure() {
  return useMutation({ mutationFn: (structureId: string) => publishFeeStructure(structureId) });
}