export type TimetableSlot = {
  id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  course_code: string;
  course_name: string;
  section: string;
  session_type: string;
  room: string | null;
  laboratory: string | null;
  status: string;
  faculty: { faculty_user_id: string; display_name: string; role: string | null }[];
};

export type TimetableDay = { anchor_date: string; slots: TimetableSlot[] };
export type TimetableWeek = { anchor_date: string; days: TimetableDay[] };
export type TimetableSemester = {
  academic_year_label: string;
  semester_label: string;
  slots: TimetableSlot[];
  cancelled_slots: TimetableSlot[];
  rescheduled_slots: TimetableSlot[];
};

export type CalendarEvent = {
  id: string;
  title: string;
  description: string | null;
  event_at: string;
  event_type: string;
  source: string;
};

export type ExaminationSchedule = {
  id: string;
  title: string;
  course_code: string;
  section: string | null;
  exam_type: string;
  scheduled_at: string;
  room: string | null;
};

export type TimetableChange = {
  id: string;
  change_type: string;
  summary: string;
  effective_at: string;
  related_session_id: string | null;
};

export type TimetableNotification = {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  created_at: string;
  read_at: string | null;
};

export type ClassSession = {
  id: string;
  course_code: string;
  section: string;
  session_type: string;
  scheduled_start: string;
  scheduled_end: string;
  room: string | null;
  laboratory: string | null;
  status: string;
  topic: string | null;
};

export type TimetableOverviewKpis = {
  classes_today: number;
  classes_this_week: number;
  next_exam_label: string | null;
  next_exam_hint: string | null;
  changes_count: number;
  changes_new_count: number;
  changes_hint: string | null;
};

export type TimetableOverviewTodayRow = {
  id: string;
  start_time: string;
  end_time: string;
  subject_label: string;
  session_type_label: string;
  room_label: string;
  faculty_label: string;
};

export type TimetableOverviewHighlight = {
  id: string;
  kind: "change" | "holiday" | "calendar";
  title: string;
  subtitle: string | null;
  badge_label: string;
  badge_tone: string;
};

export type TimetableOverviewPage = {
  page_title: string;
  anchor_date: string;
  iso_week_number: number;
  academic_year_label: string;
  semester_label: string;
  kpis: TimetableOverviewKpis;
  today_rows: TimetableOverviewTodayRow[];
  today_sessions_footer: string;
  highlights: TimetableOverviewHighlight[];
};

export type TimetableCourseFilterOption = { value: string; label: string };

export type TimetableDailySessionRow = {
  slot_id: string;
  start_time: string;
  end_time: string;
  course_code: string;
  subject_label: string;
  session_type_label: string;
  room_label: string;
  faculty_label: string;
  status_label: string;
  status_tone: string;
};

export type TimetableSessionDetail = {
  slot_id: string;
  panel_title: string;
  headline: string;
  subheadline: string | null;
  fields: { label: string; value: string }[];
};

export type TimetableDailyPage = {
  page_title: string;
  page_subtitle: string;
  anchor_date: string;
  prev_date: string;
  next_date: string;
  academic_year_label: string;
  semester_label: string;
  course_filter_options: TimetableCourseFilterOption[];
  selected_course_code: string | null;
  timeline_rows: TimetableDailySessionRow[];
  timeline_footer: string;
  session_detail: TimetableSessionDetail | null;
};

export type TimetableWeeklyDayColumn = {
  anchor_date: string;
  day_label: string;
  short_label: string;
  session_count: number;
  slots: TimetableDailySessionRow[];
};

export type TimetableWeeklyPage = {
  page_title: string;
  page_subtitle: string;
  anchor_date: string;
  academic_year_label: string;
  semester_label: string;
  course_filter_options: TimetableCourseFilterOption[];
  selected_course_code: string | null;
  days: TimetableWeeklyDayColumn[];
  week_footer: string;
};

export type TimetableMonthlyDayCell = {
  anchor_date: string;
  in_month: boolean;
  day_number: number | null;
  session_count: number;
  is_today: boolean;
};

export type TimetableMonthlyPage = {
  page_title: string;
  page_subtitle: string;
  anchor_date: string;
  academic_year_label: string;
  semester_label: string;
  weekday_labels: string[];
  weeks: TimetableMonthlyDayCell[][];
  month_footer: string;
};

export type TimetableLaboratoryPage = TimetableDailyPage & {
  page_title: string;
};