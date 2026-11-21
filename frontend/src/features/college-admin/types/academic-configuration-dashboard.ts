import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type AcademicConfigAreaRow = {
  area_key: string;
  area_label: string;
  owner_label: string;
  last_updated_label: string;
  progress_percent: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type AcademicRegulationUsageItem = {
  regulation_key: string;
  regulation_label: string;
  student_count: number;
  share_percent: number;
  tone: string;
};

export type AcademicConfigShortcut = {
  key: string;
  title: string;
  subtitle: string;
  action_label: string;
  href: string;
  icon_slug: string;
};

export type AcademicConfigSetupAlert = {
  title: string;
  description: string;
  continue_label: string;
  continue_href: string;
  deadline_label?: string | null;
};

export type AcademicConfigurationDashboardPage = {
  page_title: string;
  page_subtitle: string;
  checklist_label: string;
  checklist_href: string;
  open_current_year_label: string;
  open_current_year_href: string;
  kpis: UserDashboardKpi[];
  setup_alert: AcademicConfigSetupAlert | null;
  config_section_title: string;
  config_table_headers: string[];
  config_area_rows: AcademicConfigAreaRow[];
  config_footer_count_label: string;
  config_checklist_href: string;
  config_checklist_label: string;
  regulations_section_title: string;
  regulation_items: AcademicRegulationUsageItem[];
  shortcuts_section_title: string;
  shortcuts: AcademicConfigShortcut[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};