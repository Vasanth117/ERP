"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  bulkPrintStudentIdCards,
  fetchStudentIdCardManagementPage,
  issueStudentIdCard,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  StudentIdCardBulkPrintPayload,
  StudentIdCardIssuePayload,
  StudentIdCardManagementPageQuery,
} from "@/features/college-admin/types/student-id-card-management";

export function useStudentIdCardManagementPage(params: StudentIdCardManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentIdCardManagementPage(params),
    queryFn: () => fetchStudentIdCardManagementPage(params),
  });
}

export function useIssueStudentIdCard() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentIdCardIssuePayload) => issueStudentIdCard(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-id-card-management-page"] });
    },
  });
}

export function useBulkPrintStudentIdCards() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentIdCardBulkPrintPayload) => bulkPrintStudentIdCards(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-id-card-management-page"] });
    },
  });
}