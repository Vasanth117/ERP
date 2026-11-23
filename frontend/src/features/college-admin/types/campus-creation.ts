import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type CampusCreationWizardStep = {
  key: string;
  label: string;
  subtitle: string;
  step_number: number;
  status: string;
};

export type CampusCreationFormValues = {
  campus_code: string;
  name: string;
  is_main: string;
  address_line1: string;
  address_line2: string;
  city: string;
  district: string;
  state: string;
  country: string;
  postal_code: string;
  latitude: string;
  longitude: string;
  contact_email: string;
  contact_phone: string;
  timezone: string;
  locale: string;
  area_acres: string;
  built_up_sq_m: string;
  buildings_count: string;
  parking_slots: string;
  planned_classrooms: string;
  planned_laboratories: string;
  hostel_blocks_planned: string;
  library_branches_planned: string;
  facilities_notes: string;
};

export type CampusCreationPage = {
  draft_id: string;
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  save_draft_label: string;
  create_label: string;
  next_label: string;
  back_step_label: string;
  current_step_key: string;
  steps: CampusCreationWizardStep[];
  field_meta: InstitutionFieldMeta[];
  form: CampusCreationFormValues;
  timezone_options: InstitutionFieldOption[];
  locale_options: InstitutionFieldOption[];
  is_edit_mode: boolean;
  edit_campus_id: string | null;
  has_draft: boolean;
  generated_at: string;
};

export type CampusCreationDraftPayload = {
  draft_id?: string;
  step_key?: string;
  values?: Record<string, unknown>;
  advance?: boolean;
  retreat?: boolean;
};

export type CampusCreationFinishResult = {
  campus_id: string;
  detail_href: string;
  message: string;
};