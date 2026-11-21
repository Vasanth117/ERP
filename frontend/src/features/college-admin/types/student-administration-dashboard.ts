import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type StudentAdminDashboardFilterOption = {
  value: string;
  label: string;
};

export type StudentAdminWeeklySeriesPoint = {
  week_label: string;
  current_year_count: number;
  previous_year_count: number;
};

export type StudentAdminRecentAdmissionRow = {
  admission_id: string;
  student_name: string;
  programme_label: string;
  quota_label: string;
  admitted_label: string;
  documents_status_label: string;
  documents_status_tone: string;
  detail_href: string;
};

export type StudentAdminEnrollmentYearBar = {
  year_key: string;
  year_label: string;
  student_count: number;
  share_percent: number;
};

export type StudentAdminWorkQueueItem = {
  key: string;
  title: string;
  subtitle: string;
  count: number;
  href: string;
  action_label: string;
  icon_slug: string;
};

export type StudentAdminStatusItem = {
  status_key: string;
  status_label: string;
  student_count: number;
};

export type StudentAdminDocumentAlert = {
  title: string;
  description: string;
  continue_label: string;
  continue_href: string;
};

export type StudentAdministrationDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  new_admission_label: string;
  new_admission_href: string;
  academic_year_filter_label: string;
  programme_filter_label: string;
  study_year_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  academic_year_options: StudentAdminDashboardFilterOption[];
  programme_options: StudentAdminDashboardFilterOption[];
  study_year_options: StudentAdminDashboardFilterOption[];
  selected_academic_year: string;
  selected_programme_code: string;
  selected_study_year: string;
  kpis: UserDashboardKpi[];
  document_alert: StudentAdminDocumentAlert | null;
  admissions_chart_title: string;
  admissions_chart_current_label: string;
  admissions_chart_previous_label: string;
  admissions_weekly_series: StudentAdminWeeklySeriesPoint[];
  recent_admissions_title: string;
  recent_admissions_headers: string[];
  recent_admissions_rows: StudentAdminRecentAdmissionRow[];
  recent_admissions_footer_label: string;
  recent_admissions_view_all_href: string;
  recent_admissions_view_all_label: string;
  enrollment_by_year_title: string;
  enrollment_year_bars: StudentAdminEnrollmentYearBar[];
  work_queue_title: string;
  work_queue_items: StudentAdminWorkQueueItem[];
  student_status_title: string;
  student_status_items: StudentAdminStatusItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentAdministrationDashboardQuery = {
  academic_year_code?: string;
  programme_code?: string;
  study_year?: string;
};