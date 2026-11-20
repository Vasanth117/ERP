import type { AcademicTermSummary } from "@/features/college-admin/types/dashboard";

export type ExaminationOverviewQuery = {
  academic_year_label?: string;
  semester_label?: string;
  exam_session_id?: string;
};

export type ExaminationUpcomingSessionKpi = {
  session_name: string | null;
  session_code: string | null;
  date_range_label: string | null;
  days_to_go: number | null;
  exam_session_id: string | null;
};

export type ExaminationResultsPendingItem = {
  exam_session_id: string;
  label: string;
  session_name: string;
};

export type ExaminationOverviewKpi = {
  upcoming_session: ExaminationUpcomingSessionKpi;
  papers_scheduled: number;
  programmes_count: number;
  hall_tickets_issued: number;
  hall_tickets_total: number;
  hall_tickets_issued_pct: number | null;
  hall_tickets_withheld: number;
  results_pending_count: number;
  results_pending: ExaminationResultsPendingItem[];
};

export type ExaminationTimetableAlert = {
  title: string;
  description: string;
  submitted_at: string | null;
  timetable_id: string | null;
  review_href_note: string | null;
};

export type UpcomingExamScheduleRow = {
  row_key: string;
  date_session_label: string;
  programme_label: string;
  papers_count: number;
  candidates_count: number | null;
  halls_count: number | null;
  status_key: string;
  status_label: string;
};

export type ExaminationResultBarItem = {
  bucket_key: string;
  label: string;
  pass_rate_pct: number | null;
  student_count: number;
};

export type ExaminationReadinessItem = {
  step_key: string;
  label: string;
  description: string;
  status_key: string;
  status_label: string;
  progress_pct: number | null;
};

export type ExaminationPostResultItem = {
  item_key: string;
  label: string;
  description: string | null;
  count: number;
};

export type ExaminationOverview = {
  filters: {
    academic_year_label: string | null;
    semester_label: string | null;
    exam_session_id: string | null;
  };
  academic_term: AcademicTermSummary;
  kpis: ExaminationOverviewKpi;
  timetable_alert: ExaminationTimetableAlert | null;
  upcoming_schedule: UpcomingExamScheduleRow[];
  upcoming_schedule_total: number;
  upcoming_schedule_limit: number;
  result_summary_title: string | null;
  result_summary_bars: ExaminationResultBarItem[];
  readiness_checklist: ExaminationReadinessItem[];
  post_result_activity: ExaminationPostResultItem[];
  generated_at: string;
};