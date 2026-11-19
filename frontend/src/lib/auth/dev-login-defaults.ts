/** Matches `backend/scripts/bootstrap_dev_college_admin.py` (local seed only). */
const SEED_COLLEGE_CODE = "DEMO-COLLEGE";
const SEED_ADMIN_EMAIL = "admin@demo-college.edu";
const SEED_ADMIN_PASSWORD = "CollegeAdmin123!";

/**
 * Pre-fills the login form in local development.
 * Override via `.env.local`; never set `NEXT_PUBLIC_DEV_LOGIN_*` in production.
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