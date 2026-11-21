export type SemesterTermInput = {
  semester_number?: number | null;
  semester_label?: string | null;
} | null | undefined;

/** Display semester as a numeric value for profile and overview (not "Odd Semester"). */
export function formatStudentSemesterNumber(term: SemesterTermInput): string {
  if (term?.semester_number != null && Number.isFinite(term.semester_number)) {
    return String(term.semester_number);
  }
  const label = term?.semester_label?.trim();
  if (!label) return "—";
  const digit = label.match(/\b(\d{1,2})\b/);
  if (digit) return digit[1]!;
  return "—";
}