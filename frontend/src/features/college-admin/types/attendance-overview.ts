import type { AcademicTermSummary, DashboardDateRange } from "@/features/college-admin/types/dashboard";

export type AttendanceOverviewQuery = {
  anchor_date?: string;
  range?: DashboardDateRange;
  department_id?: string;
  programme_code?: string;
  campus_id?: string;
  academic_year_label?: string;
  semester_label?: string;
};

export type AttendanceOverviewKpi = {
  today_student_attendance_pct: number | null;
  today_students_present: number;
  today_students_total: number;
  semester_average_pct: number | null;
  semester_target_pct: number;
  semester_minimum_pct: number;
  students_below_minimum: number;
  today_faculty_attendance_pct: number | null;
  today_faculty_present: number;
  today_faculty_total: number;
};

export type DailyAttendancePoint = {
  label: string;
  session_date: string;
  attendance_pct: number | null;
  students_present: number;
  students_total: number;
};

export type AttendanceDepartmentRow = {
  department_id: string;
  department_code: string;
  department_name: string;
  student_count: number;
  today_pct: number | null;
  semester_avg_pct: number | null;
  below_minimum_count: number;
  status_key: string;
  status_label: string;
};

export type AttendanceByYearItem = {
  bucket_key: string;
  label: string;
  attendance_pct: number | null;
  student_count: number;
};

export type AttendanceCorrectionBucket = {
  bucket_key: string;
  label: string;
  count: number;
};

export type AttendanceShortageAlert = {
  alert_key: string;
  label: string;
  count: number;
};

export type AttendanceOverview = {
  filters: {
    anchor_date: string | null;
    date_range: DashboardDateRange;
    department_id: string | null;
    programme_code: string | null;
    campus_id: string | null;
    academic_year_label: string | null;
    semester_label: string | null;
  };
  academic_term: AcademicTermSummary;
  range_display_label: string | null;
  kpis: AttendanceOverviewKpi;
  daily_student_attendance: DailyAttendancePoint[];
  department_rows: AttendanceDepartmentRow[];
  department_rows_total: number;
  department_rows_limit: number;
  attendance_by_year: AttendanceByYearItem[];
  correction_requests: AttendanceCorrectionBucket[];
  shortage_alerts: AttendanceShortageAlert[];
  generated_at: string;
};