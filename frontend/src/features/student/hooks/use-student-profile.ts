"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchProfileActivities,
  fetchStudentProfile,
  updateStudentProfile,
} from "@/features/student/api/profile";
import { studentQueryKeys } from "@/features/student/query-keys";
import type { StudentProfileUpdate } from "@/features/student/types/profile";

export function useStudentProfile() {
  return useQuery({
    queryKey: studentQueryKeys.profile(),
    queryFn: fetchStudentProfile,
  });
}

export function useProfileActivities(limit = 50, offset = 0) {
  return useQuery({
    queryKey: studentQueryKeys.profileActivities(limit, offset),
    queryFn: () => fetchProfileActivities(limit, offset),
  });
}

export function useUpdateStudentProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentProfileUpdate) => updateStudentProfile(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: studentQueryKeys.profile() });
      void qc.invalidateQueries({ queryKey: studentQueryKeys.dashboard() });
    },
  });
}