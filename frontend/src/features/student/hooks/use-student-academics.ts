"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAcademicDetails,
  fetchAcademicEligibility,
  fetchEnrollmentHistory,
  fetchEnrollmentRequests,
  fetchEnrollmentStatus,
  submitEnrollmentRequest,
  confirmTermEnrollment,
  updateEnrollmentDeclaration,
} from "@/features/student/api/academics";
import { studentQueryKeys } from "@/features/student/query-keys";
import type { EnrollmentRequestCreate } from "@/features/student/types/academics";

export function useAcademicDetails() {
  return useQuery({
    queryKey: studentQueryKeys.academics(),
    queryFn: fetchAcademicDetails,
    retry: false,
  });
}

export function useEnrollmentStatus() {
  return useQuery({
    queryKey: studentQueryKeys.enrollmentStatus(),
    queryFn: fetchEnrollmentStatus,
    retry: false,
  });
}

export function useEnrollmentHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.enrollmentHistory(limit, offset),
    queryFn: () => fetchEnrollmentHistory(limit, offset),
  });
}

export function useAcademicEligibility() {
  return useQuery({
    queryKey: studentQueryKeys.eligibility(),
    queryFn: fetchAcademicEligibility,
  });
}

export function useEnrollmentRequests(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.enrollmentRequests(limit, offset),
    queryFn: () => fetchEnrollmentRequests(limit, offset),
  });
}

export function useSubmitEnrollmentRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EnrollmentRequestCreate) => submitEnrollmentRequest(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.enrollmentRequests(50, 0) });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.academics() });
    },
  });
}

export function useEnrollmentDeclaration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (accepted: boolean) => updateEnrollmentDeclaration(accepted),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.academics() });
    },
  });
}

export function useConfirmTermEnrollment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => confirmTermEnrollment(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.academics() });
    },
  });
}