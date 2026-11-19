/** Subset of backend `UserRead` — extend as modules grow. */

export type UserRole = string;

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id: string | null;
  department_id: string | null;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type LoginInput = {
  email: string;
  password: string;
  tenant_code?: string;
};