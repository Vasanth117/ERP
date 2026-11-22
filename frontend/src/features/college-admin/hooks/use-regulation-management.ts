"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { createRegulationManagement, fetchRegulationManagementPage } from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { RegulationManagementCreatePayload } from "@/features/college-admin/types/regulation-management";

export function useRegulationManagementPage(regulation_code?: string) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.regulationManagement(regulation_code),
    queryFn: () => fetchRegulationManagementPage(regulation_code),
  });
}

export function useCreateRegulationManagement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RegulationManagementCreatePayload) => createRegulationManagement(payload),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.regulationManagement() });
      toast.success("Regulation draft created");
      return data;
    },
    onError: (err: Error) => toast.error(err.message || "Could not create regulation"),
  });
}