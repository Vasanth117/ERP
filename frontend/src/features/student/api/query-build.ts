export function optionalQuery(params: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") q.set(key, value);
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}