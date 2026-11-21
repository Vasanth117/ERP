/** Paths that always require a college code at sign-in. */
/** Student/parent portals use implicit college context (per-database deployment). */
const TENANT_LOGIN_PREFIXES = [
  "/college-admin",
  "/department-admin",
  "/faculty",
  "/hr",
  "/library",
  "/hostel",
  "/examination",
  "/finance",
  "/accounts",
] as const;

export function requiresTenantCodeForNext(nextPath: string | null | undefined): boolean {
  if (!nextPath?.startsWith("/")) {
    return false;
  }
  return TENANT_LOGIN_PREFIXES.some(
    (prefix) => nextPath === prefix || nextPath.startsWith(`${prefix}/`),
  );
}

export type RawLoginInput = {
  email?: string;
  password?: string;
  tenant_code?: string | null;
};

/** Aligns with backend `LoginRequest` (`str_strip_whitespace`). */
export function normalizeLoginPayload(input: RawLoginInput): {
  email: string;
  password: string;
  tenant_code?: string;
} {
  const email = (input.email ?? "").trim().toLowerCase();
  const password = (input.password ?? "").trim();
  const tenantRaw = (input.tenant_code ?? "").trim();
  return {
    email,
    password,
    ...(tenantRaw ? { tenant_code: tenantRaw } : {}),
  };
}