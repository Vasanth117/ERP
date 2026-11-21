export type UserDashboardFilterOption = {
  value: string;
  label: string;
};

export type UserDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type UserDashboardDailyPoint = {
  date_label: string;
  active_users: number;
};

export type UserDashboardRoleBar = {
  key: string;
  label: string;
  count: number;
  progress_percent: number;
};

export type UserDashboardRecentRow = {
  user_id: string;
  user_name: string;
  role_label: string;
  department_label: string;
  created_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type UserDashboardSecurityItem = {
  key: string;
  title: string;
  description: string;
  count: number;
  tone: string;
};

import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type UserListFilterOption = {
  value: string;
  label: string;
};

export type UserListTableRow = {
  user_id: string;
  full_name: string;
  public_id: string;
  role_label: string;
  department_label: string;
  last_login_label: string;
  mfa_label: string;
  mfa_tone: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type AllUsersListPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  create_user_label: string;
  create_user_href: string;
  bulk_actions_label: string;
  bulk_actions_href: string;
  search_placeholder: string;
  role_filter_label: string;
  department_filter_label: string;
  status_filter_label: string;
  role_options: UserListFilterOption[];
  department_options: UserListFilterOption[];
  status_options: UserListFilterOption[];
  users_section_title: string;
  accounts_count_label: string;
  table_headers: string[];
  users: UserListTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type UserDetailsProfileBadge = {
  key: string;
  label: string;
  tone: string;
};

export type UserDetailsAccountField = {
  key: string;
  label: string;
  value: string;
  tone?: string | null;
};

export type UserDetailsAssignedRoleRow = {
  role_name: string;
  scope_label: string;
  assigned_by_label: string;
  since_label: string;
};

export type UserDetailsPermissionBar = {
  key: string;
  label: string;
  description: string;
  progress_percent: number;
};

export type UserDetailsActivityItem = {
  key: string;
  title: string;
  subtitle: string;
  tone: string;
};

export type UserDetailsPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  user_id: string;
  reset_password_label: string;
  suspend_label: string;
  edit_user_label: string;
  reset_password_action_user_id: string;
  suspend_href: string;
  edit_user_href: string;
  show_suspend_action: boolean;
  profile_initials: string;
  profile_name: string;
  profile_badges: UserDetailsProfileBadge[];
  designation_line: string;
  email: string;
  phone_label: string;
  last_login_summary: string;
  account_section_title: string;
  account_edit_href: string;
  account_edit_label: string;
  account_fields: UserDetailsAccountField[];
  roles_section_title: string;
  assign_role_href: string;
  assign_role_label: string;
  roles_table_headers: string[];
  assigned_roles: UserDetailsAssignedRoleRow[];
  active_roles_footer_label: string;
  role_assignment_href: string;
  role_assignment_label: string;
  permissions_section_title: string;
  permission_bars: UserDetailsPermissionBar[];
  activity_section_title: string;
  access_history_href: string;
  access_history_label: string;
  recent_activity: UserDetailsActivityItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type UserManagementDashboardPage = {
  page_title: string;
  page_subtitle: string;
  bulk_invite_label: string;
  bulk_invite_href: string;
  create_user_label: string;
  create_user_href: string;
  date_range_filter_label: string;
  role_filter_label: string;
  department_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  date_range_options: UserDashboardFilterOption[];
  role_options: UserDashboardFilterOption[];
  department_options: UserDashboardFilterOption[];
  kpis: UserDashboardKpi[];
  daily_active_title: string;
  daily_active_points: UserDashboardDailyPoint[];
  accounts_by_role_title: string;
  role_bars: UserDashboardRoleBar[];
  recent_accounts_title: string;
  recent_accounts: UserDashboardRecentRow[];
  recent_accounts_footer_label: string;
  view_all_href: string;
  view_all_label: string;
  security_checks_title: string;
  security_audit_href: string;
  security_audit_label: string;
  security_items: UserDashboardSecurityItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};