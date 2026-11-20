import type { ApiPage } from "@/features/college-admin/types/dashboard";

/** Backend list endpoints return either `T[]` or paginated `{ items, total, ... }`. */
export function itemsFromListResponse<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }
  if (data && typeof data === "object") {
    const page = data as ApiPage<T>;
    if (Array.isArray(page.items)) {
      return page.items;
    }
  }
  return [];
}

export function totalFromListResponse(data: unknown): number {
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const page = data as ApiPage<unknown>;
    if (typeof page.total === "number") {
      return page.total;
    }
    if (Array.isArray(page.items)) {
      return page.items.length;
    }
  }
  if (Array.isArray(data)) {
    return data.length;
  }
  return 0;
}