"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  addAcademicCalendarEvent,
  fetchAcademicCalendarConfigurationPage,
  publishAcademicCalendarConfiguration,
} from "@/features/college-admin/api/academics";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type {
  AcademicCalendarAddEventPayload,
  AcademicCalendarPublishPayload,
} from "@/features/college-admin/types/academic-calendar-configuration";

export type AcademicCalendarPageParams = {
  view?: string;
  page?: number;
  academic_year_id?: string;
  month?: string;
  term_id?: string;
};

export function useAcademicCalendarConfigurationPage(params?: AcademicCalendarPageParams) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.academicCalendarConfiguration(params),
    queryFn: () => fetchAcademicCalendarConfigurationPage(params),
  });
}

export function useAddAcademicCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AcademicCalendarAddEventPayload) => addAcademicCalendarEvent(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicCalendarConfiguration() });
    },
  });
}

export function usePublishAcademicCalendarConfiguration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AcademicCalendarPublishPayload) => publishAcademicCalendarConfiguration(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: collegeAdminQueryKeys.academicCalendarConfiguration() });
    },
  });
}