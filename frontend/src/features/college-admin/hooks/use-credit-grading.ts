"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  fetchCreditConfigurationPage,
  fetchGradingSystemConfigurationPage,
  resetCreditConfiguration,
  saveCreditConfiguration,
  saveGradingSystemConfiguration,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  CreditConfigurationSavePayload,
  GradingSystemConfigurationSavePayload,
} from "@/features/college-admin/types/credit-grading";

export function useCreditConfigurationPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.creditConfiguration(),
    queryFn: fetchCreditConfigurationPage,
  });
}

export function useSaveCreditConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreditConfigurationSavePayload) => saveCreditConfiguration(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.creditConfiguration() });
      toast.success("Credit rules saved");
    },
    onError: (err: Error) => toast.error(err.message || "Could not save credit rules"),
  });
}

export function useResetCreditConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: resetCreditConfiguration,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.creditConfiguration() });
      toast.success("Credit rules reset");
    },
    onError: (err: Error) => toast.error(err.message || "Could not reset"),
  });
}

export function useGradingSystemConfigurationPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.gradingSystemConfiguration(),
    queryFn: fetchGradingSystemConfigurationPage,
  });
}

export function useSaveGradingSystemConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: GradingSystemConfigurationSavePayload) => saveGradingSystemConfiguration(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.gradingSystemConfiguration() });
      toast.success("Grading rules saved");
    },
    onError: (err: Error) => toast.error(err.message || "Could not save grading rules"),
  });
}