import type { UserDashboardKpi } from "@/features/college-admin/types/faculty-workload-management";
import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type EmployeeDocumentVerificationTableRow = {
  document_id: string;
  employee_name: string;
  document_label: string;
  uploaded_label: string;
  status_label: string;
  status_tone: string;
  is_selected: boolean;
};

export type EmployeeDocumentVerificationPage = {
  page_title: string;
  page_subtitle: string;
  request_document_label: string;
  request_document_href: string;
  verify_all_label: string;
  kpis: UserDashboardKpi[];
  documents_section_title: string;
  documents_footer_label: string;
  table_headers: string[];
  document_rows: EmployeeDocumentVerificationTableRow[];
  preview_title: string;
  preview_empty_label: string;
  preview_file_name?: string | null;
  preview_meta_label?: string | null;
  browse_files_label: string;
  browse_files_href?: string | null;
  decision_section_title: string;
  result_field_label: string;
  remarks_field_label: string;
  result_options: InstitutionFieldOption[];
  selected_document_id?: string | null;
  decision_result: string;
  decision_remarks: string;
  submit_decision_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};