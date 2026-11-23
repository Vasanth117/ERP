import { apiBaseUrl } from "@/lib/env";
import { type ApiResponse, unwrapApiData } from "@/lib/api/envelope";
import { applyAuthHeaders } from "@/lib/api/auth-headers";
import {
  invalidJsonUserMessage,
  parseResponseJson,
} from "@/lib/api/parse-response-body";
import { normalizeFormPayload } from "@/lib/form-values";

function messageFromApiError(
  json: ApiResponse<unknown> | null,
  response: Response,
): string {
  const fallback = `Request failed (${response.status} ${response.statusText})`;
  const message = json?.error?.message ?? fallback;
  const details = json?.error?.details;
  if (!details?.length) {
    return message;
  }
  const first = details[0] as { msg?: string; message?: string };
  const detail = first?.message ?? first?.msg;
  if (detail && (message === "Request validation failed" || message === fallback)) {
    return detail;
  }
  return message;
}

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

  let requestBody: BodyInit | undefined = rawBody;
  if (requestBody === undefined && body !== undefined) {
    if (typeof body === "string") {
      requestBody = body;
    } else {
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
      requestBody = JSON.stringify(jsonBody);
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: requestBody,
      signal,
      credentials: "include",
    });
  } catch {
    const err = new Error(
      "Unable to reach the server. Check your connection and try again.",
    ) as Error & { status?: number; code?: string; requestId?: string | null };
    err.status = 0;
    throw err;
  }

  const requestId = response.headers.get("x-request-id");
  let json: ApiResponse<T> | null = null;

  if (response.status !== 204) {
    const parsed = await parseResponseJson<ApiResponse<T>>(response);
    if (!parsed.ok) {
      const message =
        parsed.reason === "empty" && !response.ok
          ? `Request failed (${response.status} ${response.statusText})`
          : invalidJsonUserMessage(response);
      const err = new Error(message) as Error & {
        status?: number;
        code?: string;
        requestId?: string | null;
        details?: Record<string, unknown>[];
      };
      err.status = response.status;
      err.requestId = requestId;
      throw err;
    }
    json = parsed.data;
  }

  if (!response.ok) {
    const message = messageFromApiError(json, response);
    const err = new Error(message) as Error & {
      status?: number;
      code?: string;
      requestId?: string | null;
      details?: Record<string, unknown>[];
    };
    err.status = response.status;
    err.code = json?.error?.code;
    err.details = json?.error?.details;
    err.requestId = requestId ?? json?.meta?.request_id;
    throw err;
  }

  if (response.status === 204 || json === null) {
    return undefined as T;
  }

  return unwrapApiData(json);
}