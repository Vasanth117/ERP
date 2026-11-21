import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type DepartmentResourceKpiCard = {
  key: string;
  title: string;
  value: string;
  subtitle: string;
  subtitle_tone: string;
};

export type DepartmentResourceTab = {
  department_id: string;
  label: string;
  short_label: string;
};

export type DepartmentResourceLabRow = {
  lab_id: string;
  lab_name: string;
  room_label: string;
  capacity: number;
  systems_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentResourceBudgetBar = {
  key: string;
  label: string;
  spent_label: string;
  cap_label: string;
  spent_amount: number;
  cap_amount: number;
};

export type DepartmentResourceOpenRequestItem = {
  request_id: string;
  title: string;
  detail_line: string;
  status_tag: string;
  status_tone: string;
};

export type DepartmentResourceManagementPage = {
  page_title: string;
  page_subtitle: string;
  request_resource_label: string;
  request_resource_href: string;
  faculty_nav_label: string;
  faculty_nav_href: string;
  updated_at_label: string;
  department_tabs: DepartmentResourceTab[];
  more_departments_label: string;
  more_department_options: InstitutionFieldOption[];
  selected_department_id: string;
  kpi_cards: DepartmentResourceKpiCard[];
  laboratories_section_title: string;
  laboratories_table_headers: string[];
  laboratory_rows: DepartmentResourceLabRow[];
  laboratories_footer_count_label: string;
  laboratories_view_all_label: string;
  laboratories_view_all_href: string | null;
  budget_section_title: string;
  budget_bars: DepartmentResourceBudgetBar[];
  open_requests_section_title: string;
  open_requests: DepartmentResourceOpenRequestItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};