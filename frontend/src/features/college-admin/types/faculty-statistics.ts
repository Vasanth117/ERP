import type {
  AcademicTermSummary,
  DashboardDateRange,
} from "@/features/college-admin/types/dashboard";
import type { DistributionItem } from "@/features/college-admin/types/student-statistics";

export type FacultyStatisticsFilters = {
  anchor_date: string | null;
  date_range: DashboardDateRange;
  department_id: string | null;
  designation: string | null;
  campus_id: string | null;
};

export type FacultyStatisticsKpis = {
  teaching_faculty_total: number;
  teaching_faculty_regular: number;
  teaching_faculty_visiting: number;
  non_teaching_staff_total: number;
  non_teaching_staff_detail: string | null;
  student_faculty_ratio_display: string | null;
  student_faculty_ratio_students_per_faculty: number | null;
  regulatory_ratio_max: number | null;
  regulatory_ratio_label: string | null;
  regulatory_ratio_meets_norm: boolean | null;
  open_positions_total: number;
  open_positions_teaching: number;
  open_positions_non_teaching: number;
};

export type FacultyDepartmentCountItem = {
  department_id: string | null;
  department_code: string;
  department_name: string;
  faculty_count: number;
};

export type RecentJoinerRow = {
  user_id: string;
  full_name: string;
  designation: string | null;
  department_name: string | null;
  joined_on: string | null;
  onboarding_status: string;
  onboarding_label: string;
};

export type AvailabilityOverviewItem = {
  status_key: string;
  label: string;
  description: string;
  count: number;
};

export type FacultyStatisticsOverview = {
  filters: FacultyStatisticsFilters;
  academic_term: AcademicTermSummary;
  kpis: FacultyStatisticsKpis;
  faculty_by_department: FacultyDepartmentCountItem[];
  recently_joined: RecentJoinerRow[];
  recently_joined_count: number;
  recently_joined_window_days: number;
  qualification_mix: DistributionItem[];
  designation_mix: DistributionItem[];
  availability_today: AvailabilityOverviewItem[];
  availability_anchor_date: string | null;
  designation_filter_options: string[];
  generated_at: string;
};

export type FacultyStatisticsQuery = {
  anchor_date?: string;
  range?: DashboardDateRange;
  department_id?: string;
  designation?: string;
  campus_id?: string;
};