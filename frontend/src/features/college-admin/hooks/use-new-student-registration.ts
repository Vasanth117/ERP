"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchNewStudentRegistrationPage,
  saveNewStudentRegistrationDraft,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { NewStudentRegistrationDraftPayload } from "@/features/college-admin/types/new-student-registration";

export function useNewStudentRegistrationPage(admissionId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.newStudentRegistrationPage(admissionId),
    queryFn: () => fetchNewStudentRegistrationPage(admissionId),
  });
}

export function useSaveNewStudentRegistrationDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: NewStudentRegistrationDraftPayload) => saveNewStudentRegistrationDraft(payload),
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.newStudentRegistrationPage(data.admission_id),
        data,
      );
    },
  });
}