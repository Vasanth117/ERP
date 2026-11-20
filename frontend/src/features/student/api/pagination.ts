export function pageQuery(limit = 50, offset = 0): string {
  const q = new URLSearchParams();
  q.set("limit", String(limit));
  q.set("offset", String(offset));
  return q.toString();
}