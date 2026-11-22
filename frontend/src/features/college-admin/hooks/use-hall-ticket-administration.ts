import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  fetchHallTicketAdministrationPage,
  generateAllHallTickets,
  releaseHallTickets,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useHallTicketAdministrationPage(params: { page?: number; session_id?: string } = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hallTicketAdministrationPage(params),
    queryFn: () => fetchHallTicketAdministrationPage(params),
  });
}

export function useGenerateAllHallTickets() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: generateAllHallTickets,
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.hallTicketAdministrationPage({ session_id: data.selected_session_id, page: data.pagination.page }),
        data,
      );
    },
  });
}

export function useReleaseHallTickets() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: releaseHallTickets,
    onSuccess: (data) => {
      void client.setQueryData(
        collegeAdminQueryKeys.hallTicketAdministrationPage({ session_id: data.selected_session_id, page: data.pagination.page }),
        data,
      );
    },
  });
}