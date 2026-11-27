import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchExamTimetableManagementPage,
  publishExamTimetable,
  regenerateExamTimetable,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  ExamTimetableManagementActionPayload,
  ExamTimetableManagementPageQuery,
} from "@/features/college-admin/types/exam-timetable-management";

export function useExamTimetableManagementPage(params: ExamTimetableManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examTimetableManagementPage(params),
    queryFn: () => fetchExamTimetableManagementPage(params),
  });
}

export function useRegenerateExamTimetable() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExamTimetableManagementActionPayload) => regenerateExamTimetable(payload),
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examTimetableManagementPage({
          session_id: data.selected_session_id || variables.session_id,
          programme_code: data.selected_programme_code || variables.programme_code || undefined,
          page: variables.page ?? data.pagination.page,
        }),
        data,
      );
      void client.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "exam-timetable-management-page"],
      });
    },
  });
}

export function usePublishExamTimetable() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExamTimetableManagementActionPayload) => publishExamTimetable(payload),
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examTimetableManagementPage({
          session_id: data.selected_session_id || variables.session_id,
          programme_code: data.selected_programme_code || variables.programme_code || undefined,
          page: variables.page ?? data.pagination.page,
        }),
        data,
      );
      void client.invalidateQueries({
        queryKey: [...collegeAdminQueryKeys.all, "exam-timetable-management-page"],
      });
    },
  });
}