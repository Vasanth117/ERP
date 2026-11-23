export type StudentTransferCreatePage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  submit_label: string;
  student_field_label: string;
  transfer_type_field_label: string;
  programme_field_label: string;
  section_field_label: string;
  institution_field_label: string;
  effective_field_label: string;
  reason_field_label: string;
  student_options: { value: string; label: string }[];
  transfer_type_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  effective_options: { value: string; label: string }[];
  generated_at: string;
};

export type StudentTransferCreatePayload = {
  student_record_id: string;
  transfer_type: "programme" | "section" | "outgoing";
  to_programme_code?: string;
  to_section_code?: string;
  to_institution_label?: string;
  effective_semester?: string;
  reason: string;
};

export type StudentTransferCreateResult = {
  request_key: string;
  transfer_href: string;
};