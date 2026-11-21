import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";

export type NewStudentRegistrationFormValues = {
  full_name: string;
  date_of_birth: string | null;
  gender: string | null;
  blood_group: string | null;
  mobile: string;
  email: string;
  nationality: string | null;
  community: string | null;
  guardian_name: string;
  relationship: string | null;
  guardian_mobile: string;
  occupation: string;
};

export type NewStudentRegistrationPage = {
  admission_id: string;
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  save_draft_label: string;
  continue_label: string;
  current_step_key: string;
  step_position_label: string;
  steps: { key: string; label: string; step_number: number; status: string }[];
  sections: { key: string; title: string }[];
  field_meta: InstitutionFieldMeta[];
  gender_options: { value: string; label: string }[];
  blood_group_options: { value: string; label: string }[];
  nationality_options: { value: string; label: string }[];
  community_options: { value: string; label: string }[];
  relationship_options: { value: string; label: string }[];
  form: NewStudentRegistrationFormValues;
  admission_summary_title: string;
  admission_summary: { key: string; label: string; value: string }[];
  next_steps_title: string;
  next_steps: { key: string; label: string; status_label: string; tone: string }[];
  has_draft: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type NewStudentRegistrationDraftPayload = {
  admission_id: string;
  step_key?: string;
  advance?: boolean;
  values: Record<string, unknown>;
};