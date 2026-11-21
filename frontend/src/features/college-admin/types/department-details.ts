import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type DepartmentDetailsBadge = {
  key: string;
  label: string;
  tone: string;
};

export type DepartmentDetailsProgrammeRow = {
  programme_id: string;
  programme_name: string;
  level_label: string;
  intake: number | null;
  student_count: number;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentDetailsFacultyRow = {
  user_id: string;
  name: string;
  designation: string;
  workload_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentDetailsResourceItem = {
  key: string;
  title: string;
  value: string;
};

export type DepartmentDetailsActivityItem = {
  activity_id: string;
  title: string;
  occurred_label: string;
  tone: string;
};

export type DepartmentDetailsPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  view_report_label: string;
  view_report_href: string;
  edit_department_label: string;
  edit_department_href: string;
  department_id: string;
  department_name: string;
  department_code: string;
  metadata_line: string;
  head_label: string;
  email_label: string;
  phone_label: string;
  profile_badges: DepartmentDetailsBadge[];
  kpis: UserDashboardKpi[];
  programmes_section_title: string;
  programme_mapping_href: string;
  programme_mapping_label: string;
  programmes: DepartmentDetailsProgrammeRow[];
  programmes_total: number;
  programmes_footer_label: string;
  programmes_view_all_href: string;
  faculty_section_title: string;
  faculty_allocation_href: string;
  faculty_allocation_label: string;
  faculty: DepartmentDetailsFacultyRow[];
  faculty_total: number;
  faculty_footer_label: string;
  faculty_view_all_href: string;
  resources_section_title: string;
  resources: DepartmentDetailsResourceItem[];
  activity_section_title: string;
  activities: DepartmentDetailsActivityItem[];
  table_programme_headers: string[];
  table_faculty_headers: string[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};