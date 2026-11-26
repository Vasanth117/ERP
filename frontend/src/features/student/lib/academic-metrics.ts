import type { AcademicDetails, AcademicEligibility } from "@/features/student/types/academics";

/** Programme title from API — no client-side degree prefixing. */
export function programmeDisplayName(data: AcademicDetails | null | undefined): string {
  if (!data) return "—";
  return (
    data.admission.programme_name?.trim() ||
    data.department_programme.programme_name?.trim() ||
    data.admission.programme_code?.trim() ||
    "—"
  );
}

export function currentSemesterNumber(data: AcademicDetails | null | undefined): number | null {
  const n = data?.academic_information?.current_semester_number;
  return n != null && Number.isFinite(n) ? n : null;
}

export function totalProgrammeSemesters(data: AcademicDetails | null | undefined): number | null {
  const n = data?.academic_information?.total_semesters;
  return n != null && Number.isFinite(n) ? n : null;
}

export function minimumCreditsRequired(
  data: AcademicDetails | AcademicEligibility | null | undefined,
): number | null {
  if (!data) return null;
  if ("academic_information" in (data as AcademicDetails)) {
    const fromInfo = (data as AcademicDetails).academic_information?.minimum_credits_required;
    if (fromInfo != null && Number.isFinite(fromInfo)) return fromInfo;
    const summary = (data as AcademicDetails).academic_record?.eligibility_summary;
    return creditsFromSummary(summary);
  }
  return creditsFromSummary((data as AcademicEligibility).eligibility_summary);
}

function creditsFromSummary(summary: Record<string, unknown> | undefined): number | null {
  if (!summary) return null;
  for (const key of ["minimum_credits_required", "credits_required"]) {
    const raw = summary[key];
    if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  }
  return null;
}

export function enrollmentStatusLabel(status: string | null | undefined): string {
  if (!status?.trim()) return "—";
  const upper = status.trim().toUpperCase();
  if (upper === "ACTIVE") return "Active";
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}