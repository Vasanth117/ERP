/** Trim strings and map empty optional fields to null for API payloads. */
export function normalizeFormPayload(
  values: Record<string, unknown>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(values)) {
    if (typeof value === "string") {
      const trimmed = value.trim();
      out[key] = trimmed === "" ? null : trimmed;
    } else if (value !== undefined) {
      out[key] = value;
    }
  }
  return out;
}