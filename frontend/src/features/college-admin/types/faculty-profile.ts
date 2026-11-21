import type { StudentDetailsBadge, StudentDetailsKeyValueRow } from "@/features/college-admin/types/student-details";

export type FacultyProfileQualificationRow = {
  degree: string;
  institution: string;
  year_label: string;
};

export type FacultyProfileSubjectRow = {
  subject_name: string;
  subject_code: string;
  programme_sem_label: string;
  hours_label: string;
  type_label: string;
};

export type FacultyProfilePage = {
  page_title: string;
  page_subtitle: string;
  edit_label: string;
  edit_href: string;
  timetable_label: string;
  timetable_href: string;
  back_href: string;
  back_label: string;
  record_id: string;
  profile_initials: string;
  profile_name: string;
  status_badge: StudentDetailsBadge;
  employment_type_badge: StudentDetailsBadge | null;
  profile_summary_line: string;
  email: string;
  phone: string;
  joined_label: string;
  qualifications_section_title: string;
  qualifications_headers: string[];
  qualification_rows: FacultyProfileQualificationRow[];
  qualifications_footer_label: string;
  subjects_section_title: string;
  subjects_headers: string[];
  subject_rows: FacultyProfileSubjectRow[];
  subjects_footer_label: string;
  employment_section_title: string;
  employment_rows: StudentDetailsKeyValueRow[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};