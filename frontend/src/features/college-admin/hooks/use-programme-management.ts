"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createProgrammeManagement,
  fetchProgrammeManagementPage,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { ProgrammeManagementCreatePayload } from "@/features/college-admin/types/programme-management";

export function useProgrammeManagementPage(
  params: {
    page?: number;
    search?: string;
    level_filter?: string;
    department_id?: string;
    regulation_filter?: string;
    status_filter?: string;
  } = {},
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.programmeManagement(params),
    queryFn: () => fetchProgrammeManagementPage(params),
  });
}

export function useCreateProgrammeManagement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProgrammeManagementCreatePayload) => createProgrammeManagement(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.programmeManagement() });
      toast.success("Programme created");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Could not create programme");
    },
  });
}