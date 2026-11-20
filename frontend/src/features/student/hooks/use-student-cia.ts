"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchCiaComponents,
  fetchCiaCorrections,
  fetchCiaHistory,
  fetchCiaMarks,
  fetchCiaSchedules,
  fetchCiaSubjectMarks,
  fetchCiaSummary,
} from "@/features/student/api/cia";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useCiaSummary() {
  return useQuery({
    queryKey: studentQueryKeys.ciaSummary(),
    queryFn: fetchCiaSummary,
  });
}

export function useCiaSchedules() {
  return useQuery({
    queryKey: studentQueryKeys.ciaSchedules(),
    queryFn: fetchCiaSchedules,
  });
}

export function useCiaMarks() {
  return useQuery({
    queryKey: studentQueryKeys.ciaMarks(),
    queryFn: fetchCiaMarks,
  });
}

export function useCiaSubjectMarks() {
  return useQuery({
    queryKey: studentQueryKeys.ciaSubjectMarks(),
    queryFn: fetchCiaSubjectMarks,
  });
}

export function useCiaCorrections(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.ciaCorrections(limit, offset),
    queryFn: () => fetchCiaCorrections(limit, offset),
  });
}

export function useCiaHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.ciaHistory(limit, offset),
    queryFn: () => fetchCiaHistory(limit, offset),
  });
}

export function useCiaComponents(assessmentId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.ciaComponents(assessmentId ?? ""),
    queryFn: () => fetchCiaComponents(assessmentId!),
    enabled: Boolean(assessmentId),
  });
}