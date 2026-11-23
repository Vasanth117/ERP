"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchOrganizationalHierarchyPage } from "@/features/college-admin/api/organization";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function useOrganizationalHierarchyPage(selectedNodeId?: string, editMode?: boolean) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.organizationalHierarchyPage(selectedNodeId, editMode),
    queryFn: () => fetchOrganizationalHierarchyPage(selectedNodeId, editMode),
  });
}