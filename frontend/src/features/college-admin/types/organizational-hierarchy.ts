export type OrganizationalHierarchyNode = {
  node_id: string;
  node_type: string;
  title: string;
  subtitle: string;
  depth: number;
  icon_slug: string;
  badge_label: string | null;
  badge_tone: string | null;
  status_label: string | null;
  status_tone: string | null;
  default_expanded: boolean;
  children: OrganizationalHierarchyNode[];
};

export type OrganizationalHierarchyEditAction = {
  action_key: string;
  label: string;
  href: string;
  action_type: string;
};

export type OrganizationalHierarchySelectedUnit = {
  node_id: string;
  unit_label: string;
  reports_to_label: string;
  head_label: string;
  members_label: string;
  edit_actions: OrganizationalHierarchyEditAction[];
};

export type OrganizationalHierarchySummaryItem = {
  key: string;
  label: string;
  value: string;
};

export type OrganizationalHierarchyPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  edit_structure_label: string;
  edit_structure_href: string;
  edit_mode: boolean;
  edit_panel_title: string;
  edit_panel_hint: string;
  setup_edit_actions: OrganizationalHierarchyEditAction[];
  structure_section_title: string;
  structure_section_hint: string;
  tree: OrganizationalHierarchyNode[];
  selected_unit: OrganizationalHierarchySelectedUnit | null;
  summary_section_title: string;
  summary_items: OrganizationalHierarchySummaryItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};