"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelCourseRegistration,
  fetchAvailableCourses,
  fetchConfirmedRegistrations,
  fetchElectiveGroups,
  fetchElectiveOptions,
  fetchRegistrationEligibility,
  fetchRegistrationHistory,
  submitRegistration,
  validateRegistration,
} from "@/features/student/api/registration";
import { studentQueryKeys } from "@/features/student/query-keys";
import type { RegistrationSelectionInput } from "@/features/student/types/registration";

export function useRegistrationEligibility() {
  return useQuery({
    queryKey: studentQueryKeys.registrationEligibility(),
    queryFn: fetchRegistrationEligibility,
  });
}

export function useAvailableCourses() {
  return useQuery({
    queryKey: studentQueryKeys.availableCourses(),
    queryFn: fetchAvailableCourses,
  });
}

export function useElectiveGroups() {
  return useQuery({
    queryKey: studentQueryKeys.electiveGroups(),
    queryFn: fetchElectiveGroups,
  });
}

export function useElectiveOptions(groupId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.electiveOptions(groupId ?? ""),
    queryFn: () => fetchElectiveOptions(groupId!),
    enabled: Boolean(groupId),
  });
}

export function useConfirmedRegistrations() {
  return useQuery({
    queryKey: studentQueryKeys.confirmedRegistrations(),
    queryFn: fetchConfirmedRegistrations,
  });
}

export function useRegistrationHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.registrationHistory(limit, offset),
    queryFn: () => fetchRegistrationHistory(limit, offset),
  });
}

export function useValidateRegistration() {
  return useMutation({
    mutationFn: (selections: RegistrationSelectionInput[]) =>
      validateRegistration(selections),
  });
}

export function useSubmitRegistration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (selections: RegistrationSelectionInput[]) => submitRegistration(selections),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.confirmedRegistrations() });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.registrationHistory(50, 0) });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.availableCourses() });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.dashboard() });
    },
  });
}

export function useCancelRegistration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => cancelCourseRegistration(courseId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.confirmedRegistrations() });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.registrationHistory(50, 0) });
    },
  });
}