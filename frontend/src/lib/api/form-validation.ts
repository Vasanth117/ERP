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
  return details
    .map((row) => {
      if (!row || typeof row !== "object") return null;
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
      if (!field_key) return null;
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
      return {
        field_key,
        label,
        message,
        action_type: item.action_type === "navigate" ? "navigate" : "scroll",
        action_label:
          typeof item.action_label === "string" ? item.action_label : `Go to ${label}`,
        action_href: typeof item.action_href === "string" ? item.action_href : null,
      } satisfies FormValidationDetail;
    })
    .filter((row): row is FormValidationDetail => row !== null);
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