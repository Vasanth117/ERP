"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  fetchCourseConfigurationPage,
  fetchCurriculumManagementPage,
  fetchSubjectManagementPage,
  saveCourseConfiguration,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { CourseConfigurationSavePayload } from "@/features/college-admin/types/course-curriculum";

export function useSubjectManagementPage(
  params: {
    page?: number;
    search?: string;
    department_id?: string;
    type_filter?: string;
    regulation_filter?: string;
    semester_filter?: string;
  } = {},
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.subjectManagement(params),
    queryFn: () => fetchSubjectManagementPage(params),
  });
}

export function useCurriculumManagementPage(params?: { programme_id?: string; semester?: number }) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.curriculumManagement(params),
    queryFn: () => fetchCurriculumManagementPage(params),
  });
}

export function useCourseConfigurationPage(params?: { course_id?: string; mode?: string }) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.courseConfiguration(params),
    queryFn: () => fetchCourseConfigurationPage(params),
  });
}

export function useSaveCourseConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CourseConfigurationSavePayload) => saveCourseConfiguration(payload),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.courseConfiguration() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.subjectManagement() });
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.curriculumManagement() });
      toast.success("Course saved");
      return data;
    },
    onError: (err: Error) => toast.error(err.message || "Could not save course"),
  });
}