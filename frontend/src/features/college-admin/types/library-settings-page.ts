import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type LibrarySettingsFormValues = {
  student_borrow_limit: string;
  faculty_borrow_limit: string;
  loan_period_days: string;
  renewals_allowed: string;
  fine_per_day: string;
  reservation_hold_days: string;
  block_unpaid_fines: boolean;
  send_due_reminders: boolean;
  allow_external_members: boolean;
};

export type LibrarySettingsToggleRule = {
  key: string;
  label: string;
  description: string;
  badge_label: string;
  enabled: boolean;
};

export type LibrarySettingsPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  borrowing_rules_section_title: string;
  controls_section_title: string;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  form: LibrarySettingsFormValues;
  toggle_rules: LibrarySettingsToggleRule[];
  generated_at: string;
};