import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examTimetableManagementPage({
          session_id: data.selected_session_id,
          programme_code: data.selected_programme_code || undefined,
          page: data.pagination.page,
        }),
        data,
      );
    },
  });
}

export function usePublishExamTimetable() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExamTimetableManagementActionPayload) => publishExamTimetable(payload),
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examTimetableManagementPage({
          session_id: data.selected_session_id,
          programme_code: data.selected_programme_code || undefined,
          page: data.pagination.page,
        }),
        data,
      );
    },
  });
}