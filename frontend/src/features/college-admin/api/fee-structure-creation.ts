import { apiRequest } from "@/lib/api/client";

import type { FeeStructureCreationPage, FeeStructureUpsertPayload } from "@/features/college-admin/types/fee-structure-creation";

export function fetchFeeStructureCreationPage() {
  return apiRequest<FeeStructureCreationPage>("/college-admin/finance-administration/fee-structures/create/page");
}

export function saveFeeStructure(payload: FeeStructureUpsertPayload) {
  return apiRequest<{ structure_id: string }>("/college-admin/finance-administration/fee-structures", {
    method: "PUT",
    body: payload,
  });
}

export function publishFeeStructure(structureId: string) {
  return apiRequest<{ structure_id: string }>(
    `/college-admin/finance-administration/fee-structures/${encodeURIComponent(structureId)}/publish`,
    { method: "POST" },
  );
}