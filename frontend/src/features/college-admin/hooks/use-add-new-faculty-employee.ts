"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAddNewFacultyEmployee,
  fetchAddNewFacultyEmployeePage,
  saveAddNewFacultyEmployeeDraft,
} from "@/features/college-admin/api/faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { AddNewFacultyEmployeeDraftPayload } from "@/features/college-admin/types/add-new-faculty-employee";

export function useAddNewFacultyEmployeePage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.addNewFacultyEmployeePage(),
    queryFn: () => fetchAddNewFacultyEmployeePage(),
  });
}

export function useSaveAddNewFacultyEmployeeDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddNewFacultyEmployeeDraftPayload) => saveAddNewFacultyEmployeeDraft(payload),
    onSuccess: (data) => {
      void client.setQueryData(collegeAdminQueryKeys.addNewFacultyEmployeePage(), data);
    },
  });
}

export function useCreateAddNewFacultyEmployee() {
  return useMutation({
    mutationFn: (payload: { draft_id: string; values?: Record<string, unknown> }) =>
      createAddNewFacultyEmployee(payload),
  });
}