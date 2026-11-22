import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchExaminationSessionManagementPage } from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ExaminationSessionManagementPageQuery } from "@/features/college-admin/types/examination-session-management";

export function useExaminationSessionManagementPage(params: ExaminationSessionManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examinationSessionManagementPage(params),
    queryFn: () => fetchExaminationSessionManagementPage(params),
  });
}