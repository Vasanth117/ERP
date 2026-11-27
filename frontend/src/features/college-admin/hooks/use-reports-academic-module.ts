"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";

import {
  fetchReportsModulePage,
  runReportsModuleReport,
} from "@/features/college-admin/api/reports-academic-module";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  ReportsAcademicPageQuery,
  ReportsModuleSection,
} from "@/features/college-admin/types/reports-academic-module";

export function useReportsModulePage(
  section: ReportsModuleSection,
  pageKey: string,
  params?: ReportsAcademicPageQuery,
) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsModulePage(section, pageKey, params),
    queryFn: () => fetchReportsModulePage(section, pageKey, params),
    enabled: Boolean(pageKey),
  });
}

export function useReportsAcademicModulePage(pageKey: string, params?: ReportsAcademicPageQuery) {
  return useReportsModulePage("academic", pageKey, params);
}

export function useRunReportsModuleReport(
  section: ReportsModuleSection,
  pageKey: string,
  params?: ReportsAcademicPageQuery,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => runReportsModuleReport(section, pageKey),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: collegeAdminQueryKeys.reportsModulePage(section, pageKey, params),
      });
    },
  });
}

export function useRunReportsAcademicReport(pageKey: string, params?: ReportsAcademicPageQuery) {
  return useRunReportsModuleReport("academic", pageKey, params);
}