import type { AcademicDetails } from "@/features/student/types/academics";
import type { StudentProfile } from "@/features/student/types/profile";

import type { ProfileCorrectionFieldName } from "./profile-correction-fields";

function guardianByRole(
  profile: StudentProfile,
  role: "father" | "mother",
): (typeof profile.guardians extends (infer G)[] | undefined ? G : never) | undefined {
  const list = profile.guardians ?? [];
  return list.find((g) => {
    const rel = g.relationship.toLowerCase();
    return role === "father" ? rel.includes("father") || rel.includes("parent") : rel.includes("mother");
  });
}

function formatDob(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function profileCorrectionCurrentValue(
  field: ProfileCorrectionFieldName,
  profile: StudentProfile,
  academics?: AcademicDetails | null,
): string {
  const op = profile.official_personal;
  const info = academics?.academic_information;

  switch (field) {
    case "display_name":
      return profile.full_name ?? "";
    case "roll_number":
      return profile.roll_number ?? "";
    case "admission_number":
      return profile.admission_number ?? "";
    case "programme_name":
      return profile.programme_name ?? academics?.department_programme?.programme_name ?? "";
    case "programme_code":
      return profile.programme_code ?? academics?.department_programme?.programme_code ?? "";
    case "section_code":
      return profile.section_code ?? "";
    case "batch_label":
      return info?.batch_display ?? profile.batch_label ?? academics?.admission?.batch_label ?? "";
    case "regulation_label":
      return info?.regulation_label ?? "";
    case "admission_type":
      return info?.admission_type ?? "";
    case "date_of_birth":
      return formatDob(op?.date_of_birth);
    case "gender":
      return op?.gender ?? "";
    case "nationality":
      return op?.nationality ?? "";
    case "mother_tongue":
      return op?.mother_tongue ?? "";
    case "blood_group":
      return op?.blood_group ?? "";
    case "religion":
      return op?.religion ?? "";
    case "community":
      return op?.community ?? "";
    case "aadhaar":
      return op?.aadhaar_masked ?? "";
    case "guardian_father_name":
      return guardianByRole(profile, "father")?.name ?? "";
    case "guardian_mother_name":
      return guardianByRole(profile, "mother")?.name ?? "";
    case "guardian_father_phone":
      return guardianByRole(profile, "father")?.phone ?? "";
    case "guardian_mother_phone":
      return guardianByRole(profile, "mother")?.phone ?? "";
    case "guardian_father_email":
      return guardianByRole(profile, "father")?.email ?? "";
    case "guardian_mother_email":
      return guardianByRole(profile, "mother")?.email ?? "";
    case "guardian_father_occupation":
      return guardianByRole(profile, "father")?.occupation ?? "";
    case "guardian_mother_occupation":
      return guardianByRole(profile, "mother")?.occupation ?? "";
    default:
      return "";
  }
}