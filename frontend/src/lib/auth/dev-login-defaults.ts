/** Matches `backend/scripts/bootstrap_dev_college_admin.py` (local seed only). */
const SEED_COLLEGE_CODE = "DEMO-COLLEGE";
const SEED_ADMIN_EMAIL = "admin@demo-college.edu";
const SEED_ADMIN_PASSWORD = "CollegeAdmin123!";

/** Matches `backend/scripts/bootstrap_dev_portal_users.py`. */
export const SEED_STUDENT_ID = "STU-DEMO001";
export const SEED_STUDENT_PASSWORD = "StudentDemo123!";
export const SEED_PARENT_ID = "PAR-DEMO001";
export const SEED_PARENT_PASSWORD = "ParentDemo123!";

/**
 * Pre-fills the login form in local development only.
 * Values mirror MongoDB seed scripts — not hard-coded API responses.
 */
export function getDevLoginDefaults(): {
  email: string;
  password: string;
  tenant_code: string;
} {
  if (process.env.NODE_ENV !== "development") {
    return { email: "", password: "", tenant_code: "" };
  }

  return {
    email:
      process.env.NEXT_PUBLIC_DEV_LOGIN_EMAIL?.trim() || SEED_ADMIN_EMAIL,
    password:
      process.env.NEXT_PUBLIC_DEV_LOGIN_PASSWORD || SEED_ADMIN_PASSWORD,
    tenant_code:
      process.env.NEXT_PUBLIC_DEV_LOGIN_TENANT_CODE?.trim() ||
      SEED_COLLEGE_CODE,
  };
}

export function getDevStudentLoginDefaults(): {
  identifier: string;
  password: string;
} {
  if (process.env.NODE_ENV !== "development") {
    return { identifier: "", password: "" };
  }
  return {
    identifier:
      process.env.NEXT_PUBLIC_DEV_STUDENT_ID?.trim() || SEED_STUDENT_ID,
    password:
      process.env.NEXT_PUBLIC_DEV_STUDENT_PASSWORD || SEED_STUDENT_PASSWORD,
  };
}

export function getDevParentLoginDefaults(): {
  identifier: string;
  password: string;
} {
  if (process.env.NODE_ENV !== "development") {
    return { identifier: "", password: "" };
  }
  return {
    identifier:
      process.env.NEXT_PUBLIC_DEV_PARENT_ID?.trim() || SEED_PARENT_ID,
    password:
      process.env.NEXT_PUBLIC_DEV_PARENT_PASSWORD || SEED_PARENT_PASSWORD,
  };
}