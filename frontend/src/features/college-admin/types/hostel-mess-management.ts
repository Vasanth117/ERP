import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelMessMenuRow = {
  meal_key: string;
  meal_label: string;
  menu_label: string;
  served_label: string;
};

export type HostelMessFeedbackDimension = {
  key: string;
  label: string;
  score_label: string;
  progress_percent: number;
  tone: string;
};

export type HostelMessManagementPage = {
  page_title: string;
  page_subtitle: string;
  edit_menu_label: string;
  edit_menu_href: string;
  kpis: UserDashboardKpi[];
  menu_section_title: string;
  menu_table_headers: string[];
  menu_rows: HostelMessMenuRow[];
  empty_menu_message: string;
  feedback_section_title: string;
  feedback_dimensions: HostelMessFeedbackDimension[];
  generated_at: string;
};