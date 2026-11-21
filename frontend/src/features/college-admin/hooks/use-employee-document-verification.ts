"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchEmployeeDocumentVerificationPage,
  saveEmployeeDocumentVerificationDecision,
  verifyAllEmployeeDocuments,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useEmployeeDocumentVerificationPage(documentId?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.employeeDocumentVerificationPage(documentId),
    queryFn: () => fetchEmployeeDocumentVerificationPage(documentId),
  });
}

export function useSaveEmployeeDocumentDecision(documentId?: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: saveEmployeeDocumentVerificationDecision,
    onSuccess: (data) => {
      const selected = data.selected_document_id ?? documentId ?? "";
      void client.setQueryData(
        collegeAdminQueryKeys.employeeDocumentVerificationPage(selected || undefined),
        data,
      );
      void client.invalidateQueries({
        queryKey: collegeAdminQueryKeys.employeeDocumentVerificationPage(),
      });
    },
  });
}

export function useVerifyAllEmployeeDocuments() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: verifyAllEmployeeDocuments,
    onSuccess: (data) => {
      const selected = data.selected_document_id ?? undefined;
      void client.setQueryData(collegeAdminQueryKeys.employeeDocumentVerificationPage(selected), data);
      void client.invalidateQueries({
        queryKey: collegeAdminQueryKeys.employeeDocumentVerificationPage(),
      });
    },
  });
}