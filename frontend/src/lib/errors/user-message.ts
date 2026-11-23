const TECHNICAL_ERROR_PATTERNS: RegExp[] = [
  /Failed to execute 'json' on 'Response'/i,
  /Unexpected end of JSON input/i,
  /Unexpected token.*JSON/i,
  /JSON\.parse/i,
  /NetworkError/i,
  /fetch failed/i,
  /ECONNREFUSED/i,
  /ENOTFOUND/i,
  /Load failed/i,
];

export function userFacingErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (error == null) {
    return fallback;
  }
  if (typeof error === "string") {
    const trimmed = error.trim();
    return trimmed && !isTechnicalMessage(trimmed) ? trimmed : fallback;
  }
  if (!(error instanceof Error)) {
    return fallback;
  }
  const message = error.message.trim();
  if (!message || isTechnicalMessage(message)) {
    return fallback;
  }
  return message;
}

function isTechnicalMessage(message: string): boolean {
  return TECHNICAL_ERROR_PATTERNS.some((pattern) => pattern.test(message));
}