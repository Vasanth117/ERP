import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LmsDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LmsDashboardCourseRow = {
  row_key: string;
  course_label: string;
  course_code: string;
  department_label: string;
  faculty_label: string;
  students_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsDashboardCompletionBar = {
  department_label: string;
  completion_percent: number;
  tone: string;
};

export type LmsDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  kpis: UserDashboardKpi[];
  courses_section_title: string;
  table_headers: string[];
  course_rows: LmsDashboardCourseRow[];
  empty_table_message: string;
  completion_section_title: string;
  completion_bars: LmsDashboardCompletionBar[];
  empty_completion_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: LmsDashboardPagination;
  generated_at: string;
};