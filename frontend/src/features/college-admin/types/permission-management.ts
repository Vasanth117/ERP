export type PermissionMatrixColumn = {
  column_key: string;
  institution_role_id: string | null;
  label: string;
  editable: boolean;
};

export type PermissionMatrixCell = {
  column_key: string;
  checked: boolean;
  editable: boolean;
};

export type PermissionMatrixRow = {
  row_key: string;
  label: string;
  permission_code: string;
  cells: PermissionMatrixCell[];
};

export type PermissionMatrixGroup = {
  group_key: string;
  group_label: string;
  rows: PermissionMatrixRow[];
};

export type PermissionManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_matrix_label: string;
  save_changes_label: string;
  matrix_section_title: string;
  matrix_legend: string;
  permission_columns: string[];
  columns: PermissionMatrixColumn[];
  groups: PermissionMatrixGroup[];
  unsaved_changes_title: string;
  unsaved_changes_note: string;
  change_on_label: string;
  change_off_label: string;
  can_save: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type PermissionManagementMatrixChange = {
  institution_role_id: string;
  permission_code: string;
  granted: boolean;
};