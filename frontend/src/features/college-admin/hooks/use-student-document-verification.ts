"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchStudentDocumentVerificationPage,
  saveStudentDocumentVerificationDecision,
  verifyAllStudentDocuments,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentDocumentVerificationPage(recordId?: string, documentKey?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentDocumentVerificationPage(recordId, documentKey),
    queryFn: () => fetchStudentDocumentVerificationPage(recordId, documentKey),
  });
}

export function useSaveStudentDocumentDecision(recordId: string, documentKey?: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: saveStudentDocumentVerificationDecision,
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.studentDocumentVerificationPage(recordId, data.selected_document_key ?? documentKey),
        data,
      );
    },
  });
}

export function useVerifyAllStudentDocuments(recordId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => verifyAllStudentDocuments(recordId),
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.studentDocumentVerificationPage(recordId, data.selected_document_key ?? undefined),
        data,
      );
    },
  });
}