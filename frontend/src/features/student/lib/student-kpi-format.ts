import type { FeeSummaryRead } from "@/features/student/types/dashboard";

/** Human-readable fee display — never surface raw `not_configured` in the UI. */
export function formatStudentFeesKpi(fees: FeeSummaryRead): { value: string; hint: string; tone: "warning" | "muted" } {
  const status = fees.status?.toLowerCase() ?? "";

  if (status === "not_configured" && fees.outstanding_amount == null) {
    return { value: "—", hint: "No fee record yet", tone: "muted" };
  }

  const value =
    fees.outstanding_amount != null
      ? fees.currency.toUpperCase() === "INR"
        ? `₹${fees.outstanding_amount.toLocaleString("en-IN")}`
        : `${fees.currency} ${fees.outstanding_amount.toLocaleString()}`
      : status === "not_configured"
        ? "—"
        : "0";

  const hint = fees.due_date
    ? `Due ${formatShortDate(fees.due_date)}`
    : fees.outstanding_amount != null && fees.outstanding_amount > 0
      ? "Outstanding balance"
      : "No outstanding balance";

  return {
    value,
    hint,
    tone: fees.outstanding_amount != null && fees.outstanding_amount > 0 ? "warning" : "muted",
  };
}

export function formatCgpaKpi(cgpa: number | null | undefined, creditsEarned?: number): { value: string; hint: string } {
  if (cgpa == null) {
    return { value: "—", hint: "No GPA published yet" };
  }
  const hint =
    creditsEarned != null ? `${creditsEarned} credits earned` : "Cumulative GPA for published results";
  return { value: cgpa.toFixed(2), hint };
}

export function formatBacklogKpi(
  pending: number | undefined,
  cleared?: number,
  registered?: number,
): { value: string; hint: string } {
  const p = pending ?? 0;
  const hint =
    p === 0
      ? "No pending arrear courses"
      : cleared != null && registered != null
        ? `${cleared} cleared · ${registered} registered`
        : "Pending arrear courses";
  return { value: String(p), hint };
}

function formatShortDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function courseDisplayName(
  courseCode: string,
  sources: { course_code: string; course_name?: string | null }[],
): string {
  const hit = sources.find((s) => s.course_code === courseCode);
  return hit?.course_name?.trim() || courseCode;
}