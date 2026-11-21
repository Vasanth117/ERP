import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import type { StudentDetailsBadge } from "@/features/college-admin/types/student-details";

export type EmployeeProfileManagementFormValues = {
  full_name: string;
  mobile: string;
  official_email: string;
  emergency_contact: string;
  address: string;
  reason_for_change: string;
};

export type EmployeeProfilePickerRow = {
  record_id: string;
  employee_name: string;
  employee_id_label: string;
  manage_href: string;
};

export type EmployeeProfileManagementPage = {
  page_title: string;
  page_subtitle: string;
  discard_label: string;
  save_changes_label: string;
  requires_record: boolean;
  select_employee_title?: string | null;
  select_employee_hint?: string | null;
  employee_directory_href?: string | null;
  employee_directory_label?: string | null;
  picker_rows: EmployeeProfilePickerRow[];
  record_id?: string | null;
  faculty_record_id?: string | null;
  detail_href?: string | null;
  profile_initials?: string | null;
  profile_name?: string | null;
  profile_badges: StudentDetailsBadge[];
  profile_summary_line?: string | null;
  email_display?: string | null;
  phone_display?: string | null;
  joined_label?: string | null;
  editable_section_title: string;
  field_meta: InstitutionFieldMeta[];
  form: EmployeeProfileManagementFormValues;
  locked_fields_title: string;
  locked_fields: { label: string; subtitle: string; icon_key: string }[];
  last_updated_title: string;
  last_updated?: { updated_by_label: string; updated_at_label: string; reason_label?: string | null } | null;
  audit_footer_note: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};