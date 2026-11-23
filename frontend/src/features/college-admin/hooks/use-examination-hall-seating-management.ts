"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  autoAllocateHallSeating,
  confirmHallSeating,
  fetchExaminationHallSeatingManagementPage,
} from "@/features/college-admin/api/examinations";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ExaminationHallSeatingManagementPageQuery } from "@/features/college-admin/types/examination-hall-seating-management";

export function useExaminationHallSeatingManagementPage(params: ExaminationHallSeatingManagementPageQuery = {}) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.examinationHallSeatingManagementPage(params),
    queryFn: () => fetchExaminationHallSeatingManagementPage(params),
  });
}

export function useAutoAllocateHallSeating() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: autoAllocateHallSeating,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examinationHallSeatingManagementPage({
          page: variables.page,
          session_id: variables.session_id,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}

export function useConfirmHallSeating() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: confirmHallSeating,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.examinationHallSeatingManagementPage({
          page: variables.page,
          session_id: variables.session_id,
        }),
        data,
      );
      void client.invalidateQueries({ queryKey: collegeAdminQueryKeys.all });
    },
  });
}