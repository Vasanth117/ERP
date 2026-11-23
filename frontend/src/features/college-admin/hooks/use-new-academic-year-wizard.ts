"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchNewAcademicYearWizardPage,
  saveAcademicYearWizardDraft,
} from "@/features/college-admin/api/academics";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AcademicYearWizardDraftPayload } from "@/features/college-admin/types/new-academic-year-wizard";
import { userFacingErrorMessage } from "@/lib/errors/user-message";
import { toast } from "sonner";

export function useNewAcademicYearWizardPage(draftId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.newAcademicYearWizard(draftId),
    queryFn: () => fetchNewAcademicYearWizardPage(draftId),
  });
}

export function useSaveAcademicYearWizardDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AcademicYearWizardDraftPayload) => saveAcademicYearWizardDraft(payload),
    onSuccess: (result) => {
      if (result.page) {
        void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.newAcademicYearWizard() });
      }
      if (result.created_year_id) {
        void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicYearManagement() });
      }
    },
    onError: (err: Error) => {
      toast.error(userFacingErrorMessage(err, "Could not save your progress. Please try again."));
    },
  });
}