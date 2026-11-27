import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type ReportsAcademicTableRow = {
  row_key: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
};

export type ReportsAcademicHighlightBar = {
  bar_key: string;
  department_label: string;
  percent_value: number;
  tone: string;
};

export type ReportsAcademicPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type ReportsAcademicModulePage = {
  page_key: string;
  page_title: string;
  page_subtitle: string;
  export_label: string;
  run_report_label: string;
  academic_year_label: string;
  academic_year_options: InstitutionFieldOption[];
  department_filter_label: string;
  department_options: InstitutionFieldOption[];
  selected_department_id: string;
  scope_badge_label: string;
  updated_at_label: string;
  kpis: UserDashboardKpi[];
  reports_section_title: string;
  highlights_section_title: string;
  table_headers: string[];
  report_rows: ReportsAcademicTableRow[];
  highlight_bars: ReportsAcademicHighlightBar[];
  empty_table_message: string;
  empty_highlights_message: string;
  showing_label: string;
  pagination: ReportsAcademicPagination;
  run_report_key: string;
  generated_at: string;
};

export type ReportsAcademicPageQuery = {
  page?: number;
  page_size?: number;
  academic_year?: string;
  department_id?: string;
};

export type ReportsModuleSection = "academic" | "people" | "operations";

export const REPORTS_ACADEMIC_SLUG_TO_KEY: Record<string, string> = {
  "student-reports": "student",
  "department-reports": "department",
  "academic-performance-reports": "academic-performance",
  "attendance-reports": "attendance",
  "examination-reports": "examination",
};

export const REPORTS_PEOPLE_SLUG_TO_KEY: Record<string, string> = {
  "faculty-employee-reports": "faculty-employee",
  "hr-reports": "hr",
};

export const REPORTS_OPERATIONS_SLUG_TO_KEY: Record<string, string> = {
  "finance-reports": "finance",
  "library-reports": "library",
  "hostel-reports": "hostel",
};

export function reportsSlugToModule(
  slug: string,
): { section: ReportsModuleSection; pageKey: string } | null {
  const academicKey = REPORTS_ACADEMIC_SLUG_TO_KEY[slug];
  if (academicKey) return { section: "academic", pageKey: academicKey };
  const peopleKey = REPORTS_PEOPLE_SLUG_TO_KEY[slug];
  if (peopleKey) return { section: "people", pageKey: peopleKey };
  const operationsKey = REPORTS_OPERATIONS_SLUG_TO_KEY[slug];
  if (operationsKey) return { section: "operations", pageKey: operationsKey };
  return null;
}