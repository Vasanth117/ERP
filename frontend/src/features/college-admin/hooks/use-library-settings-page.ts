"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import { fetchLibrarySettingsPage, saveLibrarySettingsPage } from "@/features/college-admin/api/library-settings-page";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LibrarySettingsFormValues } from "@/features/college-admin/types/library-settings-page";

export function useLibrarySettingsPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.librarySettingsPage(),
    queryFn: fetchLibrarySettingsPage,
  });
}

export function useSaveLibrarySettingsPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (form: LibrarySettingsFormValues) => saveLibrarySettingsPage(form),
    onSuccess: (data) => {
      queryClient.setQueryData(collegeAdminQueryKeys.librarySettingsPage(), data);
    },
  });
}