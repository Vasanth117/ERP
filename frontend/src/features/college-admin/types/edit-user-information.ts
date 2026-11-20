import type {
  InstitutionFieldMeta,
  InstitutionFieldOption,
} from "@/features/college-admin/types/institution";

export type EditUserInformationFormValues = {
  full_name: string;
  display_name: string | null;
  official_email: string;
  personal_email: string | null;
  mobile_number: string | null;
  alternate_phone: string | null;
  department_id: string | null;
  designation: string | null;
  username: string;
  login_method: string;
  mfa_requirement: string;
  session_timeout_minutes: number;
};

export type EditUserAccountStatusCard = {
  status_label: string;
  status_tone: string;
  created_label: string;
  last_modified_label: string;
};

export type EditUserDangerAction = {
  key: string;
  title: string;
  description: string;
  href: string;
  action_label: string;
  icon: string;
  api_action?: string | null;
};

export type EditUserInformationPage = {
  page_title: string;
  page_subtitle: string;
  detail_href: string;
  discard_label: string;
  save_label: string;
  cancel_label: string;
  profile_section_title: string;
  login_section_title: string;
  account_status_section_title: string;
  danger_zone_title: string;
  profile_field_meta: InstitutionFieldMeta[];
  login_field_meta: InstitutionFieldMeta[];
  department_options: InstitutionFieldOption[];
  designation_options: InstitutionFieldOption[];
  login_method_options: InstitutionFieldOption[];
  mfa_options: InstitutionFieldOption[];
  session_timeout_options: InstitutionFieldOption[];
  account_status: EditUserAccountStatusCard;
  danger_actions: EditUserDangerAction[];
  form: EditUserInformationFormValues;
  audit_footer_note: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  user_id: string;
  generated_at: string;
};