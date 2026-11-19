/** Mirrors backend `app.common.envelope` */

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>[];
};

export type ApiMeta = {
  request_id?: string | null;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: ApiErrorBody | null;
  meta: ApiMeta;
};

export function unwrapApiData<T>(body: ApiResponse<T>): T {
  if (body.success && body.data !== null) {
    return body.data;
  }

  const message =
    body.error?.message ??
    "The server returned an unexpected response. Please try again.";
  const err = new Error(message) as Error & { code?: string; details?: unknown };
  err.code = body.error?.code;
  err.details = body.error?.details;
  throw err;
}