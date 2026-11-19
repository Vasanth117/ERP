import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";

export type InstitutionUser = {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
  department_id: string | null;
  campus_id: string | null;
  account_status: string;
  is_active: boolean;
  institution_roles: string[];
  last_login_at: string | null;
  created_at: string;
};

export type InstitutionRole = {
  role_id: string;
  role_code: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  created_at: string;
};

export type Permission = {
  permission_code: string;
  description: string | null;
  category: string | null;
};

export type AccessHistoryItem = {
  event_type: string;
  occurred_at: string;
  actor_id: string | null;
  ip_address: string | null;
  detail: string | null;
};

export async function fetchUsers(
  offset = 0,
  limit = 50,
): Promise<ApiPage<InstitutionUser>> {
  return apiRequest(`/college-admin/users?limit=${limit}&offset=${offset}`);
}

export async function fetchUser(userId: string): Promise<InstitutionUser> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}`);
}

export async function createUser(payload: {
  email: string;
  password: string;
  full_name: string;
  role: string;
  department_id?: string;
  campus_id?: string;
}): Promise<InstitutionUser> {
  return apiRequest("/college-admin/users", { method: "POST", body: payload });
}

export async function updateUser(
  userId: string,
  payload: { full_name?: string; department_id?: string | null; campus_id?: string | null },
): Promise<InstitutionUser> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function inviteUser(payload: {
  email: string;
  full_name: string;
  role: string;
  department_id?: string;
  campus_id?: string;
}): Promise<{ invitation_id: string; expires_at: string }> {
  return apiRequest("/college-admin/users/invite", {
    method: "POST",
    body: payload,
  });
}

export async function bulkCreateUsers(payload: {
  users: Array<{
    email: string;
    password: string;
    full_name: string;
    role: string;
  }>;
}): Promise<InstitutionUser[]> {
  return apiRequest("/college-admin/users/bulk", {
    method: "POST",
    body: payload,
  });
}

export async function activateUser(userId: string): Promise<InstitutionUser> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}/activate`, {
    method: "POST",
    body: {},
  });
}

export async function suspendUser(
  userId: string,
  reason?: string,
): Promise<InstitutionUser> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}/suspend`, {
    method: "POST",
    body: { reason: reason ?? null },
  });
}

export async function deactivateUser(userId: string): Promise<InstitutionUser> {
  return apiRequest(
    `/college-admin/users/${encodeURIComponent(userId)}/deactivate`,
    { method: "POST", body: {} },
  );
}

export async function fetchRoles(): Promise<InstitutionRole[]> {
  return apiRequest("/college-admin/roles");
}

export async function createRole(payload: {
  role_code: string;
  name: string;
  description?: string;
  permissions: string[];
}): Promise<InstitutionRole> {
  return apiRequest("/college-admin/roles", { method: "POST", body: payload });
}

export async function updateRole(
  roleId: string,
  payload: Partial<{
    name: string;
    description: string;
    permissions: string[];
  }>,
): Promise<InstitutionRole> {
  return apiRequest(`/college-admin/roles/${encodeURIComponent(roleId)}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function fetchPermissions(): Promise<Permission[]> {
  return apiRequest("/college-admin/permissions");
}

export async function assignUserRoles(
  userId: string,
  payload: { primary_role?: string; institution_role_ids?: string[] },
): Promise<InstitutionUser> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}/roles`, {
    method: "POST",
    body: payload,
  });
}

export async function fetchUserAccessHistory(
  userId: string,
): Promise<AccessHistoryItem[]> {
  return apiRequest(
    `/college-admin/users/${encodeURIComponent(userId)}/access-history`,
  );
}