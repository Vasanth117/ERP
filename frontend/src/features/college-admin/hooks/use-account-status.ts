"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  downloadAccountStatusExport,
  fetchAccountStatusPage,
  submitAccountSuspension,
} from "@/features/college-admin/api/users";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AccountStatusSuspendFormValues } from "@/features/college-admin/types/account-status";

export function useAccountStatusPage(tab: string, page: number, userId: string | null) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.accountStatusPage(tab, page, userId),
    queryFn: () => fetchAccountStatusPage(tab, page, userId),
  });
}

export function useSubmitAccountSuspension(tab: string, page: number, userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: AccountStatusSuspendFormValues) => submitAccountSuspension(form),
    onSuccess: (result) => {
      qc.setQueryData(collegeAdminQueryKeys.accountStatusPage("suspended", 1, null), result.page);
      void qc.invalidateQueries({ queryKey: [...collegeAdminQueryKeys.all, "account-status-page"] });
    },
  });
}

export function useDownloadAccountStatus(tab: string) {
  return useMutation({
    mutationFn: () => downloadAccountStatusExport(tab),
  });
}