"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import {
  fetchLmsAssessmentManagementPage,
  fetchLmsAssignmentManagementPage,
  fetchLmsQuizManagementPage,
} from "@/features/college-admin/api/lms-assessments";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LmsAssessmentsPageQuery } from "@/features/college-admin/types/lms-assessments";

export function useLmsAssignmentManagementPage(params?: LmsAssessmentsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsAssignmentManagementPage(params),
    queryFn: () => fetchLmsAssignmentManagementPage(params),
  });
}

export function useLmsQuizManagementPage(params?: LmsAssessmentsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsQuizManagementPage(params),
    queryFn: () => fetchLmsQuizManagementPage(params),
  });
}

export function useLmsAssessmentManagementPage(params?: LmsAssessmentsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsAssessmentManagementPage(params),
    queryFn: () => fetchLmsAssessmentManagementPage(params),
  });
}