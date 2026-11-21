/** Matches backend `profile_correction_fields.ALLOWED_CORRECTION_FIELDS`. */

export const PROFILE_CORRECTION_FIELD_NAMES = [
  "display_name",
  "roll_number",
  "admission_number",
  "programme_name",
  "programme_code",
  "section_code",
  "batch_label",
  "regulation_label",
  "admission_type",
  "date_of_birth",
  "gender",
  "nationality",
  "mother_tongue",
  "blood_group",
  "religion",
  "community",
  "aadhaar",
  "guardian_father_name",
  "guardian_mother_name",
  "guardian_father_phone",
  "guardian_mother_phone",
  "guardian_father_email",
  "guardian_mother_email",
  "guardian_father_occupation",
  "guardian_mother_occupation",
] as const;

export type ProfileCorrectionFieldName = (typeof PROFILE_CORRECTION_FIELD_NAMES)[number];

export type ProfileCorrectionFieldGroup = "academic" | "personal" | "guardian";

export type ProfileCorrectionFieldOption = {
  value: ProfileCorrectionFieldName;
  label: string;
  helper: string;
  group: ProfileCorrectionFieldGroup;
};

export const PROFILE_CORRECTION_FIELD_OPTIONS: ProfileCorrectionFieldOption[] = [
  {
    value: "display_name",
    label: "Name spelling",
    helper: "Legal name on college records",
    group: "personal",
  },
  {
    value: "date_of_birth",
    label: "Date of birth",
    helper: "As on official ID or marksheet",
    group: "personal",
  },
  {
    value: "gender",
    label: "Gender",
    helper: "Official gender on record",
    group: "personal",
  },
  {
    value: "blood_group",
    label: "Blood group",
    helper: "Medical / ID record",
    group: "personal",
  },
  {
    value: "nationality",
    label: "Nationality",
    helper: "Citizenship on record",
    group: "personal",
  },
  {
    value: "religion",
    label: "Religion",
    helper: "As declared at admission",
    group: "personal",
  },
  {
    value: "community",
    label: "Community / category",
    helper: "Community or reservation category",
    group: "personal",
  },
  {
    value: "mother_tongue",
    label: "Mother tongue",
    helper: "Native language",
    group: "personal",
  },
  {
    value: "aadhaar",
    label: "Aadhaar number",
    helper: "12-digit Aadhaar (stored securely after approval)",
    group: "personal",
  },
  {
    value: "roll_number",
    label: "Register number",
    helper: "Official roll / register number",
    group: "academic",
  },
  {
    value: "admission_number",
    label: "Admission number",
    helper: "Admission identifier",
    group: "academic",
  },
  {
    value: "programme_name",
    label: "Programme name",
    helper: "Degree or programme title",
    group: "academic",
  },
  {
    value: "programme_code",
    label: "Programme code",
    helper: "Internal programme code",
    group: "academic",
  },
  {
    value: "section_code",
    label: "Section",
    helper: "Class section (e.g. A, B)",
    group: "academic",
  },
  {
    value: "batch_label",
    label: "Batch",
    helper: "Batch or intake year label",
    group: "academic",
  },
  {
    value: "regulation_label",
    label: "Regulation",
    helper: "Curriculum regulation year",
    group: "academic",
  },
  {
    value: "admission_type",
    label: "Admission type",
    helper: "Regular, lateral entry, etc.",
    group: "academic",
  },
  {
    value: "guardian_father_name",
    label: "Father / guardian name",
    helper: "Official guardian record",
    group: "guardian",
  },
  {
    value: "guardian_mother_name",
    label: "Mother / guardian name",
    helper: "Official guardian record",
    group: "guardian",
  },
  {
    value: "guardian_father_phone",
    label: "Father / guardian phone",
    helper: "Contact on guardian record",
    group: "guardian",
  },
  {
    value: "guardian_mother_phone",
    label: "Mother / guardian phone",
    helper: "Contact on guardian record",
    group: "guardian",
  },
  {
    value: "guardian_father_email",
    label: "Father / guardian email",
    helper: "Email on guardian record",
    group: "guardian",
  },
  {
    value: "guardian_mother_email",
    label: "Mother / guardian email",
    helper: "Email on guardian record",
    group: "guardian",
  },
  {
    value: "guardian_father_occupation",
    label: "Father / guardian occupation",
    helper: "Occupation on guardian record",
    group: "guardian",
  },
  {
    value: "guardian_mother_occupation",
    label: "Mother / guardian occupation",
    helper: "Occupation on guardian record",
    group: "guardian",
  },
];

/** Fields students may edit immediately (Path A — PATCH profile). */
export const PROFILE_SELF_EDIT_FIELDS = [
  "contact_phone",
  "alternate_contact_phone",
  "alternate_email",
  "permanent_address",
  "current_address",
  "emergency_contacts",
  "bio",
  "profile_photo_ref",
  "communication_preferences",
] as const;

/** Read-only on profile (not in Path A or B). */
export const PROFILE_READ_ONLY_FIELDS = [
  "student_id",
  "email",
  "current_semester",
  "advisors",
  "department_name",
] as const;

export function isProfileCorrectionFieldName(value: string): value is ProfileCorrectionFieldName {
  return (PROFILE_CORRECTION_FIELD_NAMES as readonly string[]).includes(value);
}

export function profileCorrectionFieldLabel(fieldName: string): string {
  return (
    PROFILE_CORRECTION_FIELD_OPTIONS.find((o) => o.value === fieldName)?.label ?? fieldName
  );
}

export function profileCorrectionFieldApprover(fieldName: string): string {
  const group = PROFILE_CORRECTION_FIELD_OPTIONS.find((o) => o.value === fieldName)?.group;
  if (group === "guardian" || group === "personal") return "Department Admin";
  return "College Admin";
}