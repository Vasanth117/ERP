export type StudentDetailsBadge = {
  key: string;
  label: string;
  tone: string;
};

export type StudentDetailsKeyValueRow = {
  key: string;
  label: string;
  value: string;
};

export type StudentDetailsDocumentRow = {
  document_key: string;
  document_label: string;
  uploaded_label: string;
  status_label: string;
  status_tone: string;
  verified_by_label: string;
};

export type StudentDetailsStandingField = {
  key: string;
  label: string;
  value: string;
  value_tone?: string | null;
};

export type StudentDetailsPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  record_id: string;
  edit_profile_label: string;
  edit_profile_href: string;
  academic_history_label: string;
  academic_history_href: string;
  profile_initials: string;
  profile_name: string;
  profile_badges: StudentDetailsBadge[];
  profile_summary_line: string;
  email: string;
  phone: string;
  admitted_label: string;
  enrollment_section_title: string;
  enrollment_rows: StudentDetailsKeyValueRow[];
  documents_section_title: string;
  documents_table_headers: string[];
  document_rows: StudentDetailsDocumentRow[];
  documents_footer_label: string;
  contact_section_title: string;
  contact_rows: StudentDetailsKeyValueRow[];
  standing_section_title: string;
  standing_fields: StudentDetailsStandingField[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};