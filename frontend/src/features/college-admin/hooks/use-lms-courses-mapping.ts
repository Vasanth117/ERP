"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import {
  fetchLmsCourseManagementPage,
  fetchLmsSubjectCourseMappingPage,
  postLmsSubjectAutoMap,
  postLmsSubjectSaveMapping,
} from "@/features/college-admin/api/lms-courses-mapping";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  LmsCourseManagementPageQuery,
  LmsSubjectCourseMappingPageQuery,
} from "@/features/college-admin/types/lms-courses-mapping";

export function useLmsCourseManagementPage(params?: LmsCourseManagementPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsCourseManagementPage(params),
    queryFn: () => fetchLmsCourseManagementPage(params),
  });
}

export function useLmsSubjectCourseMappingPage(params?: LmsSubjectCourseMappingPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsSubjectCourseMappingPage(params),
    queryFn: () => fetchLmsSubjectCourseMappingPage(params),
  });
}

export function useLmsSubjectAutoMap() {
  return useMutation({ mutationFn: postLmsSubjectAutoMap });
}

export function useLmsSubjectSaveMapping() {
  return useMutation({ mutationFn: postLmsSubjectSaveMapping });
}