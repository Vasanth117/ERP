import type { AcademicTermSummary } from "@/features/college-admin/types/dashboard";

export type DepartmentPerformanceFilters = {
  academic_year_label: string | null;
  semester_label: string | null;
  programme_code: string | null;
  programme_level: string | null;
  campus_id: string | null;
};

export type DepartmentPerformanceKpis = {
  best_pass_rate_pct: number | null;
  best_pass_rate_department_name: string | null;
  lowest_pass_rate_pct: number | null;
  lowest_pass_rate_department_name: string | null;
  average_attendance_pct: number | null;
  departments_above_attendance_threshold: number;
  departments_attendance_threshold_pct: number;
  departments_total_for_attendance: number;
  faculty_vacancies_total: number;
  faculty_vacancies_department_count: number;
};

export type DepartmentScorecardRow = {
  department_id: string;
  department_code: string;
  department_name: string;
  head_of_department: string | null;
  head_acting: boolean;
  student_count: number;
  faculty_count: number;
  pass_rate_pct: number | null;
  attendance_pct: number | null;
  average_cgpa: number | null;
  status_key: string;
  status_label: string;
};

export type DepartmentPassRateBarItem = {
  department_id: string;
  department_code: string;
  department_name: string;
  pass_rate_pct: number | null;
  status_key: string;
};

export type DepartmentAttentionItem = {
  department_id: string;
  department_name: string;
  message: string;
  status_key: string;
  status_label: string;
};

export type DepartmentPerformanceOverview = {
  filters: DepartmentPerformanceFilters;
  academic_term: AcademicTermSummary;
  semester_display_label: string | null;
  kpis: DepartmentPerformanceKpis;
  scorecard: DepartmentScorecardRow[];
  scorecard_total: number;
  scorecard_display_limit: number;
  pass_rate_by_department: DepartmentPassRateBarItem[];
  needs_attention: DepartmentAttentionItem[];
  generated_at: string;
};

export type DepartmentPerformanceQuery = {
  academic_year_label?: string;
  semester_label?: string;
  programme_code?: string;
  programme_level?: string;
  campus_id?: string;
};