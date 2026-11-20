import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type RoleAssignmentFormValues = {
  user_id: string;
  institution_role_id: string;
  scope_key: string;
  valid_from: string;
  valid_until: string;
  reason: string;
};

export type RoleAssignmentUserOption = {
  value: string;
  label: string;
};

export type RoleAssignmentRoleOption = {
  value: string;
  label: string;
  requires_approval: boolean;
  approval_notice: string | null;
};

export type RoleAssignmentCurrentRoleCard = {
  role_name: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_line: string;
};

export type RoleAssignmentRecentRow = {
  user_name: string;
  role_name: string;
  scope_label: string;
  until_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type RoleAssignmentPage = {
  page_title: string;
  page_subtitle: string;
  assignment_history_label: string;
  assignment_history_href: string;
  assign_role_label: string;
  form_section_title: string;
  form_field_meta: InstitutionFieldMeta[];
  user_options: RoleAssignmentUserOption[];
  role_options: RoleAssignmentRoleOption[];
  scope_options: InstitutionFieldOption[];
  form: RoleAssignmentFormValues;
  approval_notice: string | null;
  current_roles_section_title: string;
  current_roles: RoleAssignmentCurrentRoleCard[];
  recent_section_title: string;
  recent_table_headers: string[];
  recent_rows: RoleAssignmentRecentRow[];
  view_history_label: string;
  view_history_href: string;
  cancel_href: string;
  cancel_label: string;
  submit_label: string;
  submit_direct_label: string;
  footer_note: string;
  footer_snapshot_label: string;
  can_submit: boolean;
  generated_at: string;
};

export type RoleAssignmentSubmitResult = {
  page: RoleAssignmentPage;
  assignment_id: string;
  status: string;
  message: string;
};