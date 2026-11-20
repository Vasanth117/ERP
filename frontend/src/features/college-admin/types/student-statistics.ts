import type { AcademicTermSummary } from "@/features/college-admin/types/dashboard";

export type StudentStatisticsFilters = {
  academic_year_label: string | null;
  programme_code: string | null;
  study_year: number | null;
  department_id: string | null;
  campus_id: string | null;
};

export type StudentStatisticsKpis = {
  total_enrolled: number;
  total_enrolled_change_pct: number | null;
  total_enrolled_change_reference_year: string | null;
  new_admissions: number;
  new_admissions_intake_sanctioned: number | null;
  new_admissions_intake_fill_pct: number | null;
  hostel_residents: number;
  hostel_residents_pct_of_enrolled: number | null;
  discontinued: number;
  discontinued_pct_of_enrolled: number | null;
  discontinued_this_semester: number | null;
};

export type DepartmentEnrolmentItem = {
  department_id: string | null;
  department_code: string;
  department_name: string;
  student_count: number;
};

export type ProgrammeYearMatrixRow = {
  group_key: string;
  label: string;
  year_1: number;
  year_2: number;
  year_3: number;
  year_4: number;
  total: number;
};

export type DistributionItem = {
  key: string;
  label: string;
  count: number;
  share_pct: number | null;
};

export type StudentStatusOverviewItem = {
  status_key: string;
  label: string;
  description: string;
  count: number;
};

export type StudentStatisticsOverview = {
  filters: StudentStatisticsFilters;
  academic_term: AcademicTermSummary;
  kpis: StudentStatisticsKpis;
  enrolment_by_department: DepartmentEnrolmentItem[];
  programme_year_matrix: ProgrammeYearMatrixRow[];
  programme_matrix_student_total: number;
  programme_matrix_group_count: number;
  gender_distribution: DistributionItem[];
  admission_category: DistributionItem[];
  student_status: StudentStatusOverviewItem[];
  generated_at: string;
};

export type StudentStatisticsQuery = {
  academic_year_label?: string;
  programme_code?: string;
  study_year?: string;
  department_id?: string;
  campus_id?: string;
};