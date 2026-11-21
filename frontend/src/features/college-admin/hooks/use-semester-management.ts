"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createSemesterManagementTerm,
  fetchSemesterManagementPage,
  saveSemesterManagementSettings,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  SemesterCreatePayload,
  SemesterSettingsSavePayload,
} from "@/features/college-admin/types/semester-management";

export function useSemesterManagementPage(params?: {
  academic_year_id?: string;
  term_id?: string;
}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.semesterManagement(params),
    queryFn: () => fetchSemesterManagementPage(params),
  });
}

export function useSaveSemesterManagementSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SemesterSettingsSavePayload) => saveSemesterManagementSettings(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.semesterManagement() });
      toast.success("Semester settings saved");
    },
    onError: (err: Error) => toast.error(err.message || "Could not save settings"),
  });
}

export function useCreateSemesterManagementTerm() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SemesterCreatePayload) => createSemesterManagementTerm(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.semesterManagement() });
      toast.success("Semester created");
    },
    onError: (err: Error) => toast.error(err.message || "Could not create semester"),
  });
}