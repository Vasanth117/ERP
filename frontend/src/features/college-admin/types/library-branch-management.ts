export type LibraryBranchManagementRow = {
  branch_code: string;
  branch_name: string;
  location_label: string;
  titles_label: string;
  seats_label: string;
  hours_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryBranchManagementPage = {
  page_title: string;
  page_subtitle: string;
  add_branch_label: string;
  add_branch_href: string;
  branches_section_title: string;
  branches_count_label: string;
  table_headers: string[];
  branch_rows: LibraryBranchManagementRow[];
  empty_table_message: string;
  generated_at: string;
};