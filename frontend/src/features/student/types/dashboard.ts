export type StudentProfileSummary = {
  user_id: string;
  full_name: string;
  email: string;
  student_id: string | null;
  roll_number: string | null;
  admission_number: string | null;
  admission_date: string | null;
  department_id: string | null;
  department_name: string | null;
  programme_code: string | null;
  programme_name: string | null;
  batch_label: string | null;
  section_code: string | null;
};

export type AcademicTermInfo = {
  academic_year_label: string | null;
  semester_label: string | null;
};

export type EnrolledCourseSummary = {
  course_code: string;
  course_name: string | null;
  section_code: string;
  status: string;
};

export type TimetableSlotSummary = {
  day_of_week: number;
  start_time: string;
  end_time: string;
  course_code: string;
  course_name: string;
  section: string;
  room: string | null;
};

export type AttendanceCourseSummary = {
  course_code: string;
  section: string;
  percentage: number | null;
  sessions_held: number;
  min_required: number;
};

export type AttendanceSummaryRead = {
  status: string;
  overall_percentage: number | null;
  min_required: number | null;
  courses: AttendanceCourseSummary[];
};

export type PendingTaskSummary = {
  task_type: string;
  title: string;
  due_at: string | null;
  reference_id: string | null;
};

export type DeadlineSummary = {
  title: string;
  due_at: string;
  category: string;
};

export type NotificationSummary = {
  id: string;
  title: string;
  body: string;
  category: string;
  created_at: string;
};

export type FeeSummaryRead = {
  status: string;
  outstanding_amount: number | null;
  currency: string;
  due_date: string | null;
  details: Record<string, unknown>;
};

export type ResultSummary = {
  assessment_id: string;
  component_id: string;
  marks_obtained: number;
  max_marks: number;
  published_at: string;
};

export type QuickAction = {
  code: string;
  label: string;
  href: string | null;
  enabled: boolean;
};

export type StudentDashboard = {
  profile: StudentProfileSummary;
  academic_term: AcademicTermInfo;
  enrolled_courses: EnrolledCourseSummary[];
  attendance: AttendanceSummaryRead;
  timetable_today: TimetableSlotSummary[];
  upcoming_examinations: PendingTaskSummary[];
  pending_assignments: PendingTaskSummary[];
  published_results: ResultSummary[];
  fees: FeeSummaryRead;
  notifications: NotificationSummary[];
  pending_requests: PendingTaskSummary[];
  deadlines: DeadlineSummary[];
  quick_actions: QuickAction[];
  preferences: Record<string, unknown>;
};

export type StudentDashboardStats = {
  enrolled_course_count: number;
  pending_assignment_count: number;
  pending_request_count: number;
  attendance_overall_percentage: number | null;
  unread_notification_count: number;
};

export type StudentActivity = {
  id: string;
  activity_type: string;
  title: string;
  description: string | null;
  created_at: string;
};