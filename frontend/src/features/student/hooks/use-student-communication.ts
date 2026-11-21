"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchCommunicationPreferences,
  updateCommunicationPreferences,
  type CommunicationPreferencesUpdate,
} from "@/features/student/api/communication";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useCommunicationPreferences() {
  return useQuery({
    queryKey: studentQueryKeys.communicationPreferences(),
    queryFn: fetchCommunicationPreferences,
  });
}

export function useUpdateCommunicationPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CommunicationPreferencesUpdate) =>
      updateCommunicationPreferences(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.communicationPreferences() });
    },
  });
}