"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createCampus,
  fetchCampus,
  fetchCampuses,
  fetchConfigurationHistory,
  fetchInstitutionProfile,
  fetchInstitutionSettings,
  updateCampus,
  updateInstitutionProfile,
  updateInstitutionSettings,
} from "@/features/college-admin/api/institution";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  CampusCreate,
  CampusUpdate,
  InstitutionProfileUpdate,
  InstitutionSettingsPatch,
} from "@/features/college-admin/types/institution";

export function useInstitutionProfile() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.profile(),
    queryFn: fetchInstitutionProfile,
  });
}

export function useUpdateInstitutionProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionProfileUpdate) =>
      updateInstitutionProfile(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.profile() });
      toast.success("Institution profile saved");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useCampuses(activeOnly = false) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campuses(activeOnly),
    queryFn: () => fetchCampuses(activeOnly),
  });
}

export function useCampus(campusId: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campus(campusId),
    queryFn: () => fetchCampus(campusId),
    enabled: Boolean(campusId),
  });
}

export function useCreateCampus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusCreate) => createCampus(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
      toast.success("Campus created");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useUpdateCampus(campusId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusUpdate) => updateCampus(campusId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: collegeAdminQueryKeys.campus(campusId),
      });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.campuses() });
      toast.success("Campus updated");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useInstitutionSettings() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.settings(),
    queryFn: fetchInstitutionSettings,
  });
}

export function useUpdateInstitutionSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: InstitutionSettingsPatch) =>
      updateInstitutionSettings(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.settings() });
      toast.success("Settings saved");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useConfigurationHistory() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.configHistory(),
    queryFn: fetchConfigurationHistory,
  });
}