import type {
  AcademicTermSummary,
  HeadcountStatistics,
} from "@/features/college-admin/types/dashboard";

export type InstitutionAddress = {
  line1?: string | null;
  line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
};

export type InstitutionProfile = {
  tenant_id: string;
  tenant_code: string;
  legal_name: string;
  display_name: string;
  institution_code: string | null;
  secondary_codes: string[];
  institution_email: string | null;
  contact_phone: string | null;
  official_website: string | null;
  address: InstitutionAddress;
  institution_type: string | null;
  affiliation_name: string | null;
  affiliation_type: string | null;
  affiliation_id: string | null;
  timezone: string;
  locale: string;
  version: number;
  updated_at: string;
};

export type InstitutionProfileUpdate = Partial<
  Pick<
    InstitutionProfile,
    | "legal_name"
    | "display_name"
    | "institution_code"
    | "secondary_codes"
    | "institution_email"
    | "contact_phone"
    | "official_website"
    | "address"
    | "institution_type"
    | "affiliation_name"
    | "affiliation_type"
    | "affiliation_id"
  >
>;

export type Campus = {
  campus_id: string;
  campus_code: string;
  name: string;
  is_main: boolean;
  is_active: boolean;
  address: InstitutionAddress;
  contact_email: string | null;
  contact_phone: string | null;
  timezone: string | null;
  locale: string | null;
  updated_at: string;
};

export type CampusCreate = {
  campus_code: string;
  name: string;
  is_main?: boolean;
  address?: InstitutionAddress;
  contact_email?: string | null;
  contact_phone?: string | null;
  timezone?: string | null;
  locale?: string | null;
};

export type CampusUpdate = Partial<
  Pick<
    Campus,
    | "name"
    | "is_main"
    | "is_active"
    | "address"
    | "contact_email"
    | "contact_phone"
    | "timezone"
    | "locale"
  >
>;

export type InstitutionBranding = {
  display_name?: string;
  primary_color?: string;
  secondary_color?: string;
  logo_file_id?: string;
  favicon_file_id?: string;
  theme?: Record<string, string>;
  version?: number;
};

export type InstitutionSettings = {
  tenant_id: string;
  settings: Record<string, unknown>;
  branding: InstitutionBranding | null;
  version: number;
  updated_at: string;
};

export type InstitutionSettingsPatch = {
  locale?: string;
  timezone?: string;
  date_format?: string;
  time_format?: string;
  academic_year_display?: string;
  semester_display?: string;
  grade_display_scale?: string;
  show_department_in_reports?: boolean;
  notification_digest_enabled?: boolean;
  inter_batch_section_transfer_requires_college_approval?: boolean;
  branding?: InstitutionBranding;
};

export type ConfigurationHistoryItem = {
  scope: string;
  version_number: number;
  changed_keys: string[];
  created_at: string;
  created_by: string | null;
};

export type CampusOverviewRow = {
  campus_id: string;
  campus_code: string;
  name: string;
  is_main: boolean;
  is_active: boolean;
  location_label: string;
  student_count: number;
  department_count: number;
};

export type ProgrammeLevelMixItem = {
  level: string;
  label: string;
  student_count: number;
  programme_count: number;
};

export type ComplianceStatusItem = {
  title: string;
  status_code: string;
  detail?: string | null;
};

export type KeyContactItem = {
  name: string;
  role_label: string;
  email?: string | null;
  phone?: string | null;
};

export type InstitutionalOverview = {
  profile: InstitutionProfile;
  academic_term: AcademicTermSummary;
  statistics: HeadcountStatistics;
  accreditation_summary: string | null;
  accreditation_detail: string | null;
  campuses: CampusOverviewRow[];
  programme_mix: ProgrammeLevelMixItem[];
  compliance_items: ComplianceStatusItem[];
  key_contacts: KeyContactItem[];
  generated_at: string;
};