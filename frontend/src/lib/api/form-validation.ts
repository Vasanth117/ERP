export type FormValidationDetail = {
  field_key: string;
  label: string;
  message: string;
  action_type: "scroll" | "navigate";
  action_label: string;
  action_href?: string | null;
};

function humanizeFieldKey(fieldKey: string): string {
  return fieldKey
    .replace(/_/g, " ")
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export function parseFormValidationDetails(details: unknown): FormValidationDetail[] {
  if (!Array.isArray(details)) return [];
  const out: FormValidationDetail[] = [];
  for (const row of details) {
    if (!row || typeof row !== "object") continue;
    const item = row as Record<string, unknown>;
    let field_key =
      typeof item.field_key === "string"
        ? item.field_key
        : typeof item.field === "string"
          ? item.field
          : "";
    if (!field_key && Array.isArray(item.loc)) {
      const loc = item.loc.filter((part): part is string | number => part !== "body");
      const last = loc[loc.length - 1];
      if (typeof last === "string") field_key = last;
    }
    if (!field_key) continue;
    const label =
      typeof item.label === "string" ? item.label : humanizeFieldKey(field_key);
    const message =
      typeof item.message === "string"
        ? item.message
        : typeof item.msg === "string"
          ? item.msg
          : typeof item.subtitle === "string"
            ? item.subtitle
            : "This field is required.";
    const detail: FormValidationDetail = {
      field_key,
      label,
      message,
      action_type: item.action_type === "navigate" ? "navigate" : "scroll",
      action_label:
        typeof item.action_label === "string" ? item.action_label : `Go to ${label}`,
    };
    if (typeof item.action_href === "string") {
      detail.action_href = item.action_href;
    }
    out.push(detail);
  }
  return out;
}

export function scrollToFormField(fieldKey: string) {
  const target = document.querySelector(`[data-field-key="${fieldKey}"]`);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  const focusable = target.querySelector<HTMLElement>(
    "input:not([disabled]), select:not([disabled]), textarea:not([disabled])",
  );
  focusable?.focus({ preventScroll: true });
}