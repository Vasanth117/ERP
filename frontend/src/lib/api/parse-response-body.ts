export type ParseJsonResult<T> =
  | { ok: true; data: T }
  | { ok: false; reason: "empty" | "invalid_json" };

export async function readResponseText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

export function parseJsonText<T>(text: string): ParseJsonResult<T> {
  const trimmed = text.trim();
  if (!trimmed) {
    return { ok: false, reason: "empty" };
  }
  try {
    return { ok: true, data: JSON.parse(trimmed) as T };
  } catch {
    return { ok: false, reason: "invalid_json" };
  }
}

export async function parseResponseJson<T>(
  response: Response,
): Promise<ParseJsonResult<T>> {
  const text = await readResponseText(response);
  return parseJsonText<T>(text);
}

export function invalidJsonUserMessage(
  response: Response,
  context: "api" | "auth" = "api",
): string {
  if (context === "auth") {
    return "Sign-in is temporarily unavailable. Please try again in a moment.";
  }
  if (!response.ok) {
    return `Something went wrong (${response.status}). Please try again.`;
  }
  return "The server returned an unexpected response. Please try again.";
}