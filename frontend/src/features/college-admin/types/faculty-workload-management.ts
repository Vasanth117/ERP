import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type UserDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type FacultyWorkloadManagementTableRow = {
  record_id: string;
  faculty_name: string;
  department_label: string;
  theory_hours_label: string;
  lab_hours_label: string;
  total_hours_label: string;
  policy_hours_label: string;
  status_label: string;
  status_tone: string;
  timetable_href: string;
};

export type FacultyWorkloadManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  rebalance_label: string;
  workload_section_title: string;
  table_headers: string[];
  workload_rows: FacultyWorkloadManagementTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  kpis: UserDashboardKpi[];
  selected_academic_year: string;
  selected_semester_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type FacultyWorkloadManagementQuery = {
  page?: number;
  academic_year_label?: string;
  semester_label?: string;
};