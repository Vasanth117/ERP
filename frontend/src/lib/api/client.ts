import { apiBaseUrl } from "@/lib/env";
import { type ApiResponse, unwrapApiData } from "@/lib/api/envelope";
import { applyAuthHeaders } from "@/lib/api/auth-headers";
import { normalizeFormPayload } from "@/lib/form-values";

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
    applyAuthHeaders(requestHeaders);
  }

  let jsonBody: unknown = body;
  if (
    body &&
    typeof body === "object" &&
    !Array.isArray(body) &&
    "values" in body &&
    body.values &&
    typeof body.values === "object" &&
    !Array.isArray(body.values)
  ) {
    jsonBody = {
      ...(body as Record<string, unknown>),
      values: normalizeFormPayload(body.values as Record<string, unknown>),
    };
  }

  const response = await fetch(url, {
    method,
    headers: requestHeaders,
    body:
      rawBody ?? (jsonBody !== undefined ? JSON.stringify(jsonBody) : undefined),
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