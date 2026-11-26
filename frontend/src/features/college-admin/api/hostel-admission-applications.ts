import { apiRequest } from "@/lib/api/client";

import type {
  HostelAdmissionApplicationsPage,
  HostelAdmissionApplicationsPageQuery,
} from "@/features/college-admin/types/hostel-admission-applications";

export function fetchHostelAdmissionApplicationsPage(params?: HostelAdmissionApplicationsPageQuery) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  if (params?.academic_year_label) qs.set("academic_year_label", params.academic_year_label);
  const suffix = qs.size ? `?${qs.toString()}` : "";
  return apiRequest<HostelAdmissionApplicationsPage>(
    `/college-admin/hostel-administration/applications/management/page${suffix}`,
  );
}