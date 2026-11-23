"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  autoSuggestFacultySubjectAllocation,
  confirmFacultySubjectAllocation,
  fetchFacultySubjectAllocationPage,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { FacultySubjectAllocationQuery } from "@/features/college-admin/types/faculty-subject-allocation";

export function useFacultySubjectAllocationPage(params?: FacultySubjectAllocationQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.facultySubjectAllocationPage(params),
    queryFn: () => fetchFacultySubjectAllocationPage(params),
  });
}

export function useAutoSuggestFacultySubjectAllocation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: FacultySubjectAllocationQuery) => autoSuggestFacultySubjectAllocation(payload),
    onSuccess: (data, variables) => {
      void client.setQueryData(collegeAdminQueryKeys.facultySubjectAllocationPage(variables), data);
    },
  });
}

export function useConfirmFacultySubjectAllocation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: confirmFacultySubjectAllocation,
    onSuccess: (data, variables) => {
      void client.setQueryData(
        collegeAdminQueryKeys.facultySubjectAllocationPage({
          academic_year_label: variables.academic_year_label,
          semester_label: variables.semester_label,
          department_id: variables.department_id,
        }),
        data,
      );
    },
  });
}