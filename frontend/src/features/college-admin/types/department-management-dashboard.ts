import type { UserDashboardFilterOption, UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type DepartmentEnrollmentBar = {
  department_id: string;
  department_code: string;
  student_count: number;
  faculty_count: number;
};

export type DepartmentAttentionRow = {
  department_id: string;
  department_name: string;
  issue: string;
  owner_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type DepartmentSchoolBar = {
  school_id: string;
  school_name: string;
  department_count: number;
  share_percent: number;
};

export type DepartmentQuickAction = {
  key: string;
  title: string;
  subtitle: string;
  action_label: string;
  href: string;
  icon_slug: string;
};

export type DepartmentManagementDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  create_department_label: string;
  create_department_href: string;
  academic_year_filter_label: string;
  campus_filter_label: string;
  school_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  academic_year_options: UserDashboardFilterOption[];
  campus_options: UserDashboardFilterOption[];
  school_options: UserDashboardFilterOption[];
  selected_academic_year: string;
  selected_campus_id: string;
  selected_school_id: string;
  kpis: UserDashboardKpi[];
  enrollment_chart_title: string;
  enrollment_bars: DepartmentEnrollmentBar[];
  attention_section_title: string;
  attention_table_headers: string[];
  attention_rows: DepartmentAttentionRow[];
  attention_footer_label: string;
  attention_view_all_href: string;
  attention_view_all_label: string;
  schools_section_title: string;
  school_bars: DepartmentSchoolBar[];
  quick_actions_title: string;
  quick_actions: DepartmentQuickAction[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};