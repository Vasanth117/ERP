"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import {
  fetchLmsLearningMaterialManagementPage,
  fetchLmsVideoLectureManagementPage,
} from "@/features/college-admin/api/lms-content";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LmsLearningMaterialPageQuery, LmsVideoLecturePageQuery } from "@/features/college-admin/types/lms-content";

export function useLmsLearningMaterialManagementPage(params?: LmsLearningMaterialPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsLearningMaterialManagementPage(params),
    queryFn: () => fetchLmsLearningMaterialManagementPage(params),
  });
}

export function useLmsVideoLectureManagementPage(params?: LmsVideoLecturePageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsVideoLectureManagementPage(params),
    queryFn: () => fetchLmsVideoLectureManagementPage(params),
  });
}