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