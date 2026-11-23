"use client";

import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import { fetchFinanceSettingsPage, saveFinanceSettingsPage } from "@/features/college-admin/api/finance-settings-page";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FinanceSettingsFormValues } from "@/features/college-admin/types/finance-settings-page";

export function useFinanceSettingsPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.financeSettingsPage(),
    queryFn: fetchFinanceSettingsPage,
  });
}

export function useSaveFinanceSettingsPage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FinanceSettingsFormValues) => saveFinanceSettingsPage(form),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.financeSettingsPage() });
      toast.success("Finance settings saved");
    },
    onError: onCollegeAdminMutationError,
  });
}