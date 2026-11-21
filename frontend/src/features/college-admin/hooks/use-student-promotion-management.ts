"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchStudentPromotionManagementPage,
  previewStudentPromotion,
  promoteEligibleStudents,
} from "@/features/college-admin/api/students";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  StudentPromotionManagementPageQuery,
  StudentPromotionPromotePayload,
} from "@/features/college-admin/types/student-promotion-management";

export function useStudentPromotionManagementPage(params: StudentPromotionManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentPromotionManagementPage(params),
    queryFn: () => fetchStudentPromotionManagementPage(params),
  });
}

export function usePreviewStudentPromotion() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (params: StudentPromotionManagementPageQuery) => previewStudentPromotion(params),
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.studentPromotionManagementPage(variables), data);
    },
  });
}

export function usePromoteEligibleStudents() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentPromotionPromotePayload) => promoteEligibleStudents(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "student-promotion-management-page"] });
    },
  });
}