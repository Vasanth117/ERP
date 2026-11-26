import { useCollegeAdminMutation as useMutation } from "@/features/college-admin/hooks/use-college-admin-mutation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";
import { useQueryClient } from "@tanstack/react-query";

import {
  fetchHrEmployeeBenefitsClaimsPage,
  fetchHrPerformanceManagementPage,
  openHrPerformanceCycle,
} from "@/features/college-admin/api/hr-benefits-performance";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { HrBenefitsPageQuery } from "@/features/college-admin/types/hr-benefits-performance";

export function useHrEmployeeBenefitsClaimsPage(params?: HrBenefitsPageQuery) {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrEmployeeBenefitsClaimsPage(params),
    queryFn: () => fetchHrEmployeeBenefitsClaimsPage(params),
  });
}

export function useHrPerformanceManagementPage() {
  return useQuery({
    queryKey: collegeAdminQueryKeys.hrPerformanceManagementPage(),
    queryFn: () => fetchHrPerformanceManagementPage(),
  });
}

export function useOpenHrPerformanceCycle(cycleId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => openHrPerformanceCycle(cycleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrPerformanceManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.hrDashboardPage() });
    },
  });
}