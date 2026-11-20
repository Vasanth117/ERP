import type { AcademicTermSummary } from "@/features/college-admin/types/dashboard";
import type { DistributionItem } from "@/features/college-admin/types/student-statistics";

export type AcademicPerformanceFilters = {
  academic_year_label: string | null;
  semester_label: string | null;
  programme_code: string | null;
  study_year: number | null;
};

export type AcademicPerformanceKpis = {
  overall_pass_rate_pct: number | null;
  overall_pass_rate_change_pts: number | null;
  overall_pass_rate_reference_label: string | null;
  average_cgpa: number | null;
  average_cgpa_ug: number | null;
  average_cgpa_pg: number | null;
  first_class_distinction_pct: number | null;
  first_class_distinction_student_count: number;
  students_with_backlogs: number;
  students_with_backlogs_pct: number | null;
  students_with_three_plus_arrears: number;
};

export type PassRateTrendPoint = {
  label: string;
  college_pass_rate_pct: number | null;
  university_benchmark_pct: number | null;
};

export type PassRateByStudyYearBar = {
  bucket_key: string;
  label: string;
  pass_rate_pct: number | null;
  student_count: number;
};

export type LowPassSubjectRow = {
  course_code: string;
  course_name: string | null;
  department_code: string | null;
  department_name: string | null;
  semester_label: string | null;
  appeared_count: number;
  pass_rate_pct: number | null;
  trend_key: string;
  trend_label: string;
};

export type GradeDistributionItem = DistributionItem & {
  grade_letter?: string | null;
};

export type AcademicRiskItem = {
  risk_key: string;
  label: string;
  description: string | null;
  count: number;
};

export type TopPerformerRow = {
  user_id: string;
  full_name: string;
  programme_label: string | null;
  study_year_label: string | null;
  cgpa: number;
};

export type AcademicPerformanceOverview = {
  filters: AcademicPerformanceFilters;
  academic_term: AcademicTermSummary;
  results_display_label: string | null;
  kpis: AcademicPerformanceKpis;
  pass_rate_trend: PassRateTrendPoint[];
  pass_rate_by_study_year: PassRateByStudyYearBar[];
  low_pass_subjects: LowPassSubjectRow[];
  low_pass_subjects_below_pct: number;
  grade_distribution: GradeDistributionItem[];
  academic_risk: AcademicRiskItem[];
  top_performers: TopPerformerRow[];
  generated_at: string;
};

export type AcademicPerformanceQuery = {
  academic_year_label?: string;
  semester_label?: string;
  programme_code?: string;
  study_year?: string;
};