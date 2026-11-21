import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchExaminationConfigurationPage,
  saveExaminationConfiguration,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  ExaminationConfigurationPageQuery,
  ExaminationConfigurationSavePayload,
} from "@/features/college-admin/types/examination-configuration";

export function useExaminationConfigurationPage(params: ExaminationConfigurationPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examinationConfigurationPage(params),
    queryFn: () => fetchExaminationConfigurationPage(params),
  });
}

export function useSaveExaminationConfiguration() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExaminationConfigurationSavePayload) => saveExaminationConfiguration(payload),
    onSuccess: (data) => {
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.examinationSessionManagementPage() });
      void client.setQueryData(
        collegeAdminQueryKeys.examinationConfigurationPage({
          session_id: data.session_id ?? undefined,
        }),
        data,
      );
    },
  });
}