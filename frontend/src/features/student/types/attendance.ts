export type AttendanceMark = {
  session_id: string;
  session_date: string;
  course_code: string;
  section: string;
  status: string | null;
  verified: boolean;
};

export type SubjectAttendanceDetail = {
  course_code: string;
  section: string;
  subject_id: string | null;
  percentage: number | null;
  sessions_held: number;
  sessions_recorded: number;
  min_required: number;
  below_threshold: boolean;
  data_status: string;
};

export type AttendanceSemesterSummary = {
  academic_year_label: string;
  semester_label: string;
  overall_percentage: number | null;
  min_required: number;
  data_status: string;
  subjects: SubjectAttendanceDetail[];
  shortage_warnings: string[];
};

export type AttendanceEligibility = {
  eligible: boolean;
  overall_percentage: number | null;
  min_required: number;
  reasons: string[];
  data_status: string;
};

export type AttendanceShortage = {
  course_code: string;
  section: string;
  percentage: number | null;
  min_required: number;
  sessions_remaining_to_clear: number | null;
};

export type DiscrepancyRequestCreate = {
  session_id: string;
  claimed_status: string;
  reason: string;
};

export type DiscrepancyRequest = {
  id: string;
  session_id: string;
  course_code: string;
  section: string;
  session_date: string;
  recorded_status: string | null;
  claimed_status: string;
  reason: string;
  status: string;
  reviewer_note: string | null;
  submitted_at: string;
  resolved_at: string | null;
};

export type AttendanceSummaryExport = {
  generated_at: string;
  academic_year_label: string;
  semester_label: string;
  data_status: string;
  csv_content: string;
};