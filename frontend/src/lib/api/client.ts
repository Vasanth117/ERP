import { apiBaseUrl } from "@/lib/env";
import { type ApiResponse, unwrapApiData } from "@/lib/api/envelope";
import {
  getAccessToken,
  getTenantOverrideId,
} from "@/lib/auth/token-store";

export type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  /** Skip JSON Content-Type (e.g. FormData) */
  rawBody?: BodyInit;
  headers?: HeadersInit;
  auth?: boolean;
  signal?: AbortSignal;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    rawBody,
    headers,
    auth = true,
    signal,
  } = options;

  const url = path.startsWith("http") ? path : `${apiBaseUrl()}${path}`;

  const requestHeaders = new Headers(headers);
  if (!rawBody && body !== undefined && method !== "GET") {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
    const tenantId = getTenantOverrideId();
    if (tenantId) {
      requestHeaders.set("X-Tenant-Id", tenantId);
    }
  }

  const response = await fetch(url, {
    method,
    headers: requestHeaders,
    body:
      rawBody ?? (body !== undefined ? JSON.stringify(body) : undefined),
    signal,
    credentials: "include",
  });

  const requestId = response.headers.get("x-request-id");
  let json: ApiResponse<T> | null = null;

  if (response.status !== 204) {
    json = (await response.json()) as ApiResponse<T>;
  }

  if (!response.ok) {
    const message =
      json?.error?.message ??
      `Request failed (${response.status} ${response.statusText})`;
    const err = new Error(message) as Error & {
      status?: number;
      code?: string;
      requestId?: string | null;
    };
    err.status = response.status;
    err.code = json?.error?.code;
    err.requestId = requestId ?? json?.meta?.request_id;
    throw err;
  }

  if (response.status === 204 || json === null) {
    return undefined as T;
  }

  return unwrapApiData(json);
}