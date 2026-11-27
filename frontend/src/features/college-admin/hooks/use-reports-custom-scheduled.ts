"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import {
  createReportsSchedule,
  fetchReportsCustomBuilderPage,
  fetchReportsExportHistoryPage,
  fetchReportsScheduledPage,
  runReportsGenerate,
  saveReportsCustomBuilder,
} from "@/features/college-admin/api/reports-custom-scheduled";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  ReportsBuilderPageQuery,
  ReportsCustomBuilderSave,
  ReportsPageQuery,
  ReportsScheduleCreate,
} from "@/features/college-admin/types/reports-custom-scheduled";

export function useReportsScheduledPage(params?: ReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsScheduledPage(params),
    queryFn: () => fetchReportsScheduledPage(params),
  });
}

export function useCreateReportsSchedule(params?: ReportsPageQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReportsScheduleCreate) => createReportsSchedule(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.reportsScheduledPage(params) });
    },
  });
}

export function useReportsExportHistoryPage(params?: ReportsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsExportHistoryPage(params),
    queryFn: () => fetchReportsExportHistoryPage(params),
  });
}

export function useReportsCustomBuilderPage(params?: ReportsBuilderPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.reportsCustomBuilderPage(params),
    queryFn: () => fetchReportsCustomBuilderPage(params),
  });
}

export function useSaveReportsCustomBuilder(params?: ReportsBuilderPageQuery) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReportsCustomBuilderSave) => saveReportsCustomBuilder(body, params),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.reportsCustomBuilderPage(params) });
    },
  });
}

export function useRunReportsGenerate() {
  return useMutation({
    mutationFn: (report_key: string) => runReportsGenerate(report_key),
  });
}