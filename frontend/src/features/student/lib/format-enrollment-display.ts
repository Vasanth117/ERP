/** ST 02.02 — display helpers for official enrollment fields. */

export function formatEnrollmentSection(
  programmeCode: string | null | undefined,
  sectionCode: string | null | undefined,
): string {
  if (!sectionCode?.trim()) return "—";
  const code = programmeCode?.trim() ?? "";
  const short =
    code.includes("-") ? (code.split("-").pop() ?? code) : code.length <= 6 ? code : code.slice(-3);
  return short ? `${short.toUpperCase()}-${sectionCode.trim()}` : sectionCode.trim();
}

export function formatEnrollmentStatusLabel(status: string | null | undefined): string {
  if (!status?.trim()) return "—";
  const normalized = status.trim().replace(/_/g, " ");
  return normalized.replace(/\b\w/g, (c) => c.toUpperCase());
}