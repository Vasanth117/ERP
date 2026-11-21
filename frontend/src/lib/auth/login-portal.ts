export type LoginPortal = "default" | "institution" | "student-performance";

export function parseLoginPortal(
  value: string | null | undefined,
): LoginPortal {
  if (value === "institution" || value === "student-performance") {
    return value;
  }
  return "default";
}

export function inferLoginPortalFromNext(nextPath: string | null | undefined): LoginPortal {
  if (!nextPath?.startsWith("/")) {
    return "default";
  }
  if (nextPath === "/college-admin" || nextPath.startsWith("/college-admin/")) {
    return "institution";
  }
  if (nextPath === "/student" || nextPath.startsWith("/student/")) {
    return "student-performance";
  }
  return "default";
}

export function resolveLoginPortal(
  portalParam: string | null | undefined,
  nextPath: string | null | undefined,
): LoginPortal {
  const explicit = parseLoginPortal(portalParam);
  if (explicit !== "default") {
    return explicit;
  }
  return inferLoginPortalFromNext(nextPath);
}

const INSTITUTION_ROLES = new Set([
  "college_admin",
  "super_admin",
  "platform_admin",
  "department_admin",
]);

export function roleAllowedForPortal(
  role: string,
  portal: LoginPortal,
  signInMode: "student" | "parent",
): boolean {
  if (portal === "institution") {
    return INSTITUTION_ROLES.has(role);
  }
  if (portal === "student-performance") {
    return signInMode === "student" ? role === "student" : role === "parent";
  }
  return true;
}

export function portalTitle(portal: LoginPortal): string {
  switch (portal) {
    case "institution":
      return "Institution Management";
    case "student-performance":
      return "Student Performance";
    default:
      return "College ERP";
  }
}

export function portalWelcomeSubtitle(portal: LoginPortal): string {
  switch (portal) {
    case "institution":
      return "Sign in with your institutional email to access the admin dashboard.";
    case "student-performance":
      return "Sign in with your college-issued ID and password.";
    default:
      return "Access your dashboard with the credentials from your college.";
  }
}