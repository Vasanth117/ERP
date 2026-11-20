import type { PoliciesPagination, UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type RoleManagementTableRow = {
  role_id: string;
  role_name: string;
  role_code: string;
  type_label: string;
  users_count: number;
  modules_label: string;
  last_changed_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type RoleManagementDashboardPage = {
  page_title: string;
  page_subtitle: string;
  compare_roles_label: string;
  compare_roles_href: string;
  create_role_label: string;
  create_role_href: string;
  kpis: UserDashboardKpi[];
  roles_section_title: string;
  roles_count_label: string;
  table_headers: string[];
  roles: RoleManagementTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};