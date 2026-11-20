import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type CreateEditRoleFormValues = {
  name: string;
  role_code: string;
  base_role: string;
  scope: string;
  description: string | null;
  require_mfa: boolean;
  restrict_campus_network: boolean;
  time_bound_access: boolean;
};

export type CreateEditRolePermissionCell = {
  column_key: string;
  applicable: boolean;
  checked: boolean;
};

export type CreateEditRolePermissionRow = {
  row_key: string;
  label: string;
  cells: CreateEditRolePermissionCell[];
};

export type CreateEditRolePermissionGroup = {
  group_key: string;
  group_label: string;
  rows: CreateEditRolePermissionRow[];
};

export type CreateEditRoleAccessToggle = {
  key: string;
  label: string;
  description: string;
  checked: boolean;
};

export type CreateEditRoleAssignedUser = {
  user_id: string;
  name: string;
  subtitle: string;
  detail_href: string;
};

export type CreateEditRolePage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  cancel_href: string;
  cancel_label: string;
  save_label: string;
  type_badge_label: string;
  type_badge_tone: string;
  role_details_section_title: string;
  module_permissions_section_title: string;
  access_rules_section_title: string;
  users_with_role_section_title: string;
  assign_users_label: string;
  assign_users_href: string;
  permission_columns: string[];
  permission_groups: CreateEditRolePermissionGroup[];
  access_toggles: CreateEditRoleAccessToggle[];
  assigned_users: CreateEditRoleAssignedUser[];
  more_users_label: string | null;
  base_role_options: InstitutionFieldOption[];
  scope_options: InstitutionFieldOption[];
  role_details_field_meta: InstitutionFieldMeta[];
  form: CreateEditRoleFormValues;
  role_id: string | null;
  is_create: boolean;
  can_save: boolean;
  footer_note: string;
  generated_at: string;
};

export type CreateEditRolePermissionToggle = {
  row_key: string;
  column_key: string;
  checked: boolean;
};