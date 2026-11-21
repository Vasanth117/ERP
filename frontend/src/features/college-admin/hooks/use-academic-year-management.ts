"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  closeCurrentAcademicYear,
  createAcademicYearManagement,
  fetchAcademicYearManagementPage,
  saveAcademicYearManagementRules,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  AcademicYearManagementCreatePayload,
  AcademicYearManagementRulesPayload,
} from "@/features/college-admin/types/academic-year-management";

export function useAcademicYearManagementPage(page = 1) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicYearManagement(page),
    queryFn: () => fetchAcademicYearManagementPage(page),
  });
}

export function useCreateAcademicYearManagement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AcademicYearManagementCreatePayload) => createAcademicYearManagement(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicYearManagement() });
      toast.success("Academic year created");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Could not create academic year");
    },
  });
}

export function useCloseCurrentAcademicYear() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: closeCurrentAcademicYear,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicYearManagement() });
      toast.success("Current academic year closed");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Could not close academic year");
    },
  });
}

export function useSaveAcademicYearManagementRules() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AcademicYearManagementRulesPayload) => saveAcademicYearManagementRules(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicYearManagement() });
      toast.success("Rules updated");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Could not save rules");
    },
  });
}