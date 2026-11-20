import type { UserDashboardFilterOption, UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LoginAccountActivityDailyBar = {
  day_key: string;
  day_label: string;
  login_count: number;
};

export type LoginAccountActivityMethodBar = {
  method_key: string;
  method_label: string;
  percent: number;
};

export type LoginAccountActivityRecentRow = {
  user_name: string;
  method_label: string;
  device_label: string;
  location_label: string;
  result_code: string;
  result_label: string;
  result_tone: string;
};

export type LoginAccountActivityLockedCard = {
  user_id: string;
  user_name: string;
  subtitle: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  unlock_href: string;
};

export type LoginAccountActivityPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  date_range_options: UserDashboardFilterOption[];
  role_filter_options: UserDashboardFilterOption[];
  location_filter_options: UserDashboardFilterOption[];
  selected_date_range: string;
  selected_role_filter: string;
  selected_location_filter: string;
  scope_badge_label: string;
  updated_label: string;
  kpis: UserDashboardKpi[];
  logins_per_day_title: string;
  daily_bars: LoginAccountActivityDailyBar[];
  daily_bars_max: number;
  login_methods_title: string;
  method_bars: LoginAccountActivityMethodBar[];
  recent_section_title: string;
  recent_live_label: string;
  view_all_label: string;
  view_all_href: string;
  recent_table_headers: string[];
  recent_rows: LoginAccountActivityRecentRow[];
  locked_section_title: string;
  unlock_label: string;
  locked_accounts: LoginAccountActivityLockedCard[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};