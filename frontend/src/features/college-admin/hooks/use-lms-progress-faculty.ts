"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import {
  fetchLmsFacultyContentManagementPage,
  fetchLmsStudentLearningProgressPage,
  postLmsFacultyContentApproveSelected,
} from "@/features/college-admin/api/lms-progress-faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LmsProgressFacultyPageQuery } from "@/features/college-admin/types/lms-progress-faculty";

export function useLmsStudentLearningProgressPage(params?: LmsProgressFacultyPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsStudentLearningProgressPage(params),
    queryFn: () => fetchLmsStudentLearningProgressPage(params),
  });
}

export function useLmsFacultyContentManagementPage(params?: LmsProgressFacultyPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.lmsFacultyContentManagementPage(params),
    queryFn: () => fetchLmsFacultyContentManagementPage(params),
  });
}

export function useLmsFacultyContentApproveSelected() {
  return useMutation({ mutationFn: postLmsFacultyContentApproveSelected });
}