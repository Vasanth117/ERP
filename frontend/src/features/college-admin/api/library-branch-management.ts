import { apiRequest } from "@/lib/api/client";

import type { LibraryBranchManagementPage } from "@/features/college-admin/types/library-branch-management";

export function fetchLibraryBranchManagementPage() {
  return apiRequest<LibraryBranchManagementPage>("/college-admin/library-administration/branches/management/page");
}