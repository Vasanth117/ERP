import type { AcademicYearCreateFormOption } from "@/features/college-admin/types/academic-year-management";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";

export type AcademicYearWizardStep = {
  key: string;
  label: string;
  step_number: number;
  status: string;
};

export type AcademicYearWizardFormValues = {
  label: string;
  copy_from_year_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  admission_intake_opens?: string | null;
  summer_term_start?: string | null;
  summer_term_end?: string | null;
  year_end_closing?: string | null;
  semester_count: string;
};

export type NewAcademicYearWizardPage = {
  draft_id: string;
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  save_draft_label: string;
  continue_label: string;
  finalize_label: string;
  current_step_key: string;
  step_position_label: string;
  steps: AcademicYearWizardStep[];
  sections: { key: string; title: string }[];
  field_meta: InstitutionFieldMeta[];
  copy_from_options: AcademicYearCreateFormOption[];
  semester_count_options: AcademicYearCreateFormOption[];
  form: AcademicYearWizardFormValues;
  summary_title: string;
  summary_items: { key: string; label: string; value: string }[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AcademicYearWizardDraftPayload = {
  draft_id: string;
  step_key?: string;
  advance?: boolean;
  finalize?: boolean;
  values?: Record<string, unknown>;
};

export type NewAcademicYearWizardSaveResult = {
  page: NewAcademicYearWizardPage | null;
  created_year_id?: string | null;
  details_href?: string | null;
};