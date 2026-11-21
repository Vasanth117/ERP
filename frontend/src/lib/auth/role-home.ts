/** Default post-login destination per backend role. */
export function homePathForRole(role: string): string {
  switch (role) {
    case "student":
      return "/student/dashboard";
    case "parent":
      return "/under-construction?module=parent";
    case "college_admin":
    case "department_admin":
      return "/college-admin/dashboard";
    default:
      return "/dashboard";
  }
}