import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchStudentExamEligibilityPage, rerunStudentExamEligibility } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useStudentExamEligibilityPage(params: { page?: number; session_id?: string } = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.studentExamEligibilityPage(params),
    queryFn: () => fetchStudentExamEligibilityPage(params),
  });
}

export function useRerunStudentExamEligibility() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: rerunStudentExamEligibility,
    onSuccess: (data) => {
      void client.setQueryData(collegeAdminQueryKeys.studentExamEligibilityPage({ session_id: data.selected_session_id, page: data.pagination.page }), data);
    },
  });
}