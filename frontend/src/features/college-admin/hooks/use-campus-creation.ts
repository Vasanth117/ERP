"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchCampusCreationPage,
  finishCampusCreation,
  saveCampusCreationDraft,
} from "@/features/college-admin/api/institution";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { CampusCreationDraftPayload } from "@/features/college-admin/types/campus-creation";

export function useCampusCreationPage(campusId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.campusCreationPage(campusId),
    queryFn: () => fetchCampusCreationPage(campusId),
  });
}

export function useSaveCampusCreationDraft(campusId?: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: CampusCreationDraftPayload) => saveCampusCreationDraft(payload),
    onSuccess: (data) => {
      void client.setQueryData(collegeAdminQueryKeys.campusCreationPage(campusId), data);
    },
  });
}

export function usePatchCampusCreationStep(campusId?: string) {
  const client = useQueryClient();
  return (stepKey: string) => {
    const queryKey = collegeAdminQueryKeys.campusCreationPage(campusId);
    client.setQueryData(queryKey, (old: import("@/features/college-admin/types/campus-creation").CampusCreationPage | undefined) => {
      if (!old) return old;
      return { ...old, current_step_key: stepKey };
    });
  };
}

export function useFinishCampusCreation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: { draft_id: string; values?: Record<string, unknown> }) => finishCampusCreation(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.campusesDashboard() });
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.campuses() });
    },
  });
}