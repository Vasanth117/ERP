"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import { fetchHostelSettingsPage, saveHostelSettingsPage } from "@/features/college-admin/api/hostel-settings-page";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HostelSettingsFormValues } from "@/features/college-admin/types/hostel-settings-page";

export function useHostelSettingsPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hostelSettingsPage(),
    queryFn: fetchHostelSettingsPage,
  });
}

export function useSaveHostelSettingsPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (form: HostelSettingsFormValues) => saveHostelSettingsPage(form),
    onSuccess: (data) => {
      queryClient.setQueryData(collegeAdminQueryKeys.hostelSettingsPage(), data);
    },
  });
}