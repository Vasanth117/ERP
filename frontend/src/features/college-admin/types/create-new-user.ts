import type {
  InstitutionFieldMeta,
  InstitutionFieldOption,
} from "@/features/college-admin/types/institution";

export type CreateNewUserWizardStep = {
  key: string;
  label: string;
  step_number: number;
};

export type CreateNewUserFormSection = {
  key: string;
  title: string;
};

export type CreateNewUserToggleSetting = {
  key: string;
  label: string;
  description: string | null;
  default_on: boolean;
};

export type CreateNewUserValidationCheck = {
  key: string;
  title: string;
  subtitle: string;
  status_code: string;
  status_label: string;
  tone: string;
};

export type CreateNewUserReviewLine = {
  label: string;
  value: string;
};

export type CreateNewUserFormValues = {
  first_name: string;
  last_name: string;
  official_email: string;
  mobile_number: string;
  public_id: string;
  joining_date: string | null;
  gender: string | null;
  date_of_birth: string | null;
  user_type: string;
  department_id: string | null;
  designation: string | null;
  campus_id: string | null;
  institution_role_id: string | null;
  send_invitation_email: boolean;
  send_sms_login_link: boolean;
  require_mfa_first_login: boolean;
  allow_sso_login: boolean;
};

export type CreateNewUserPage = {
  page_title: string;
  page_subtitle: string;
  cancel_href: string;
  cancel_label: string;
  create_invite_label: string;
  save_draft_label: string;
  next_step_prefix: string;
  audit_footer_note: string;
  current_step_key: string;
  steps: CreateNewUserWizardStep[];
  sections: CreateNewUserFormSection[];
  field_meta: InstitutionFieldMeta[];
  gender_options: InstitutionFieldOption[];
  user_type_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  designation_options: InstitutionFieldOption[];
  campus_options: InstitutionFieldOption[];
  institution_role_options: InstitutionFieldOption[];
  invitation_settings: CreateNewUserToggleSetting[];
  validation_checks: CreateNewUserValidationCheck[];
  review_lines: CreateNewUserReviewLine[];
  form: CreateNewUserFormValues;
  has_draft: boolean;
  footer_disclaimer: string;
  generated_at: string;
};

export type CreateNewUserSubmitResult = {
  status: string;
  message: string;
  user_id: string | null;
  invitation_id: string | null;
  detail_href: string | null;
  accept_token: string | null;
};