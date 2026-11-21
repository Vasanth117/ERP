"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchProfileCorrections,
  submitProfileCorrection,
  type ProfileCorrectionSubmit,
} from "@/features/student/api/portal-documents";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useProfileCorrections() {
  return useQuery({
    queryKey: studentQueryKeys.profileCorrections(),
    queryFn: fetchProfileCorrections,
  });
}

export function useSubmitProfileCorrection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileCorrectionSubmit) => submitProfileCorrection(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.profileCorrections() });
    },
  });
}