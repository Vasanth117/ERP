import type { StudentDetailsBadge } from "@/features/college-admin/types/student-details";

export type FacultyTimetablePickerRow = {
  record_id: string;
  faculty_name: string;
  employee_id_label: string;
  timetable_href: string;
};

export type FacultyTimetableGridCell = {
  label: string;
  is_empty: boolean;
};

export type FacultyTimetableDayRow = {
  day_key: string;
  day_label: string;
  cells: FacultyTimetableGridCell[];
};

export type FacultyTimetablePage = {
  page_title: string;
  page_subtitle: string;
  context_line: string;
  print_label: string;
  edit_slots_label: string;
  edit_slots_href: string;
  requires_record: boolean;
  select_faculty_title?: string | null;
  select_faculty_hint?: string | null;
  faculty_directory_href?: string | null;
  faculty_directory_label?: string | null;
  picker_rows: FacultyTimetablePickerRow[];
  record_id?: string | null;
  profile_initials?: string | null;
  profile_name?: string | null;
  profile_badges: StudentDetailsBadge[];
  profile_summary_line?: string | null;
  email_display?: string | null;
  phone_display?: string | null;
  joined_label?: string | null;
  weekly_section_title: string;
  column_headers: string[];
  day_rows: FacultyTimetableDayRow[];
  timetable_footer_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};