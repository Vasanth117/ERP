import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";

export type StudentProfileManagementFormValues = {
  full_name: string;
  mobile: string;
  email: string;
  guardian_mobile: string;
  address: string;
  reason_for_change: string;
};

export type StudentProfileManagementPage = {
  page_title: string;
  page_subtitle: string;
  discard_label: string;
  save_changes_label: string;
  requires_record: boolean;
  select_student_title: string | null;
  select_student_hint: string | null;
  all_students_href: string | null;
  all_students_label: string | null;
  picker_rows: { record_id: string; student_name: string; register_number: string; manage_href: string }[];
  record_id: string | null;
  detail_href: string | null;
  profile_initials: string | null;
  profile_name: string | null;
  profile_badges: { key: string; label: string; tone: string }[];
  profile_summary_line: string | null;
  email_display: string | null;
  phone_display: string | null;
  admitted_label: string | null;
  editable_section_title: string;
  field_meta: InstitutionFieldMeta[];
  form: StudentProfileManagementFormValues;
  locked_fields_title: string;
  locked_fields: { key: string; label: string; value: string; hint: string }[];
  transfer_workflow_href: string | null;
  last_updated_title: string;
  last_updated: { by_label: string; on_label: string } | null;
  document_verification_href: string | null;
  audit_footer_note: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};