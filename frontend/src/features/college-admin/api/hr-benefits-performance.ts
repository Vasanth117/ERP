import { apiRequest } from "@/lib/api/client";

import type {
  HrBenefitsPageQuery,
  HrEmployeeBenefitsClaimsPage,
  HrPerformanceManagementPage,
} from "@/features/college-admin/types/hr-benefits-performance";

function buildQuery(params?: HrBenefitsPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchHrEmployeeBenefitsClaimsPage(params?: HrBenefitsPageQuery) {
  return apiRequest<HrEmployeeBenefitsClaimsPage>(
    `/college-admin/hr-administration/benefits/claims/page${buildQuery(params)}`,
  );
}

export function fetchHrPerformanceManagementPage() {
  return apiRequest<HrPerformanceManagementPage>("/college-admin/hr-administration/performance/management/page");
}

export function openHrPerformanceCycle(cycleId?: string) {
  const q = cycleId ? `?cycle_id=${encodeURIComponent(cycleId)}` : "";
  return apiRequest<{ cycle_id: string; status: string; reviews_created?: number; already_active?: boolean }>(
    `/college-admin/hr-administration/performance/cycles/open${q}`,
    { method: "POST" },
  );
}