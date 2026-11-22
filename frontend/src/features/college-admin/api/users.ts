import { apiRequest } from "@/lib/api/client";

import type { ApiPage } from "@/features/college-admin/types/dashboard";
import type {
  CreateNewUserPage,
  CreateNewUserSubmitResult,
  CreateNewUserValidationCheck,
  CreateNewUserReviewLine,
} from "@/features/college-admin/types/create-new-user";
import type { EditUserInformationPage } from "@/features/college-admin/types/edit-user-information";
import type {
  BulkUserInvitationPage,
  BulkUserInvitationSendResult,
} from "@/features/college-admin/types/bulk-user-invitation";
import { apiBaseUrl } from "@/lib/env";
import { applyAuthHeaders } from "@/lib/api/auth-headers";
import type {
  AllUsersListPage,
  UserDetailsPage,
  UserManagementDashboardPage,
} from "@/features/college-admin/types/user-management-dashboard";
import type { RoleManagementDashboardPage } from "@/features/college-admin/types/role-management-dashboard";
import type {
  CreateEditRoleFormValues,
  CreateEditRolePage,
  CreateEditRolePermissionToggle,
} from "@/features/college-admin/types/create-edit-role";
import type {
  PermissionManagementMatrixChange,
  PermissionManagementPage,
} from "@/features/college-admin/types/permission-management";
import type {
  RoleAssignmentFormValues,
  RoleAssignmentPage,
  RoleAssignmentSubmitResult,
} from "@/features/college-admin/types/role-assignment";
import type {
  AccountStatusPage,
  AccountStatusSuspendFormValues,
  AccountStatusSuspendResult,
} from "@/features/college-admin/types/account-status";
import type { LoginAccountActivityPage } from "@/features/college-admin/types/login-account-activity";

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

export async function fetchAllUsersListPage(params: {
  page?: number;
  search?: string;
  role_filter?: string;
  department_id?: string;
  status_filter?: string;
} = {}): Promise<AllUsersListPage> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.search) qs.set("search", params.search);
  if (params.role_filter) qs.set("role_filter", params.role_filter);
  if (params.department_id) qs.set("department_id", params.department_id);
  if (params.status_filter) qs.set("status_filter", params.status_filter);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<AllUsersListPage>(`/college-admin/users/all-users-list/page${suffix}`);
}

export async function fetchRoleManagementDashboardPage(page = 1): Promise<RoleManagementDashboardPage> {
  return apiRequest<RoleManagementDashboardPage>(`/college-admin/roles/management-dashboard/page?page=${page}`);
}

export async function fetchCreateEditRolePage(roleId: string | null): Promise<CreateEditRolePage> {
  const qs = roleId ? `?role_id=${encodeURIComponent(roleId)}` : "";
  return apiRequest<CreateEditRolePage>(`/college-admin/roles/create-edit/page${qs}`);
}

export async function saveCreateEditRole(payload: {
  role_id: string | null;
  form: CreateEditRoleFormValues;
  permission_toggles: CreateEditRolePermissionToggle[];
}): Promise<CreateEditRolePage> {
  return apiRequest<CreateEditRolePage>("/college-admin/roles/create-edit/save", {
    method: "POST",
    body: {
      role_id: payload.role_id,
      form: payload.form,
      permission_toggles: payload.permission_toggles,
    },
  });
}

export async function fetchPermissionManagementPage(): Promise<PermissionManagementPage> {
  return apiRequest<PermissionManagementPage>("/college-admin/permissions/management-matrix/page");
}

export async function savePermissionManagementMatrix(payload: {
  changes: PermissionManagementMatrixChange[];
}): Promise<PermissionManagementPage> {
  return apiRequest<PermissionManagementPage>("/college-admin/permissions/management-matrix/save", {
    method: "POST",
    body: payload,
  });
}

export async function fetchLoginAccountActivityPage(params: {
  date_range?: string;
  role_filter?: string;
  location_filter?: string;
}): Promise<LoginAccountActivityPage> {
  const qs = new URLSearchParams();
  if (params.date_range) qs.set("date_range", params.date_range);
  if (params.role_filter) qs.set("role_filter", params.role_filter);
  if (params.location_filter) qs.set("location_filter", params.location_filter);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<LoginAccountActivityPage>(`/college-admin/users/login-account-activity/page${suffix}`);
}

export async function downloadLoginAccountActivityExport(params: {
  date_range?: string;
  role_filter?: string;
  location_filter?: string;
}): Promise<void> {
  const qs = new URLSearchParams();
  if (params.date_range) qs.set("date_range", params.date_range);
  if (params.role_filter) qs.set("role_filter", params.role_filter);
  if (params.location_filter) qs.set("location_filter", params.location_filter);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}/college-admin/users/login-account-activity/export${suffix}`, {
    headers,
  });
  if (!response.ok) throw new Error("Could not export login activity");
  const text = await response.text();
  const blob = new Blob([text], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "login_account_activity.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export async function fetchAccountStatusPage(
  tab: string,
  page: number,
  userId: string | null,
): Promise<AccountStatusPage> {
  const qs = new URLSearchParams();
  qs.set("tab", tab);
  qs.set("page", String(page));
  if (userId) qs.set("user_id", userId);
  return apiRequest<AccountStatusPage>(`/college-admin/users/account-status/page?${qs.toString()}`);
}

export async function submitAccountSuspension(
  form: AccountStatusSuspendFormValues,
): Promise<AccountStatusSuspendResult> {
  return apiRequest<AccountStatusSuspendResult>("/college-admin/users/account-status/suspend", {
    method: "POST",
    body: { form },
  });
}

export async function downloadAccountStatusExport(tab: string): Promise<void> {
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(
    `${apiBaseUrl()}/college-admin/users/account-status/export?tab=${encodeURIComponent(tab)}`,
    { headers },
  );
  if (!response.ok) throw new Error("Could not export account status");
  const text = await response.text();
  const blob = new Blob([text], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `account_status_${tab}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function fetchRoleAssignmentPage(
  userId: string | null,
  roleId: string | null,
): Promise<RoleAssignmentPage> {
  const qs = new URLSearchParams();
  if (userId) qs.set("user_id", userId);
  if (roleId) qs.set("role_id", roleId);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<RoleAssignmentPage>(`/college-admin/users/role-assignment/page${suffix}`);
}

export async function submitRoleAssignment(
  form: RoleAssignmentFormValues,
): Promise<RoleAssignmentSubmitResult> {
  return apiRequest<RoleAssignmentSubmitResult>("/college-admin/users/role-assignment/submit", {
    method: "POST",
    body: { form },
  });
}

export async function downloadPermissionManagementMatrix(): Promise<void> {
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}/college-admin/permissions/management-matrix/export`, {
    headers,
  });
  if (!response.ok) throw new Error("Could not export permission matrix");
  const text = await response.text();
  const blob = new Blob([text], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "permission_matrix.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export async function fetchBulkUserInvitationPage(page = 1): Promise<BulkUserInvitationPage> {
  return apiRequest<BulkUserInvitationPage>(`/college-admin/users/bulk-user-invitation/page?page=${page}`);
}

export async function uploadBulkUserInvitation(payload: {
  file_name: string;
  file_content: string;
  file_size_bytes?: number;
}): Promise<BulkUserInvitationPage> {
  return apiRequest<BulkUserInvitationPage>("/college-admin/users/bulk-user-invitation/upload", {
    method: "POST",
    body: payload,
  });
}

export async function updateBulkUserInvitationSettings(payload: {
  step_key?: string;
  skip_rows_with_errors?: boolean;
  require_mfa_first_login?: boolean;
}): Promise<BulkUserInvitationPage> {
  return apiRequest<BulkUserInvitationPage>("/college-admin/users/bulk-user-invitation/settings", {
    method: "PUT",
    body: payload,
  });
}

export async function sendBulkUserInvitations(): Promise<BulkUserInvitationSendResult> {
  return apiRequest<BulkUserInvitationSendResult>("/college-admin/users/bulk-user-invitation/send", {
    method: "POST",
    body: {},
  });
}

export async function downloadBulkInviteTemplate(): Promise<void> {
  const headers = new Headers();
  applyAuthHeaders(headers);
  const response = await fetch(`${apiBaseUrl()}/college-admin/users/bulk-user-invitation/template`, { headers });
  if (!response.ok) throw new Error("Could not download template");
  const text = await response.text();
  const blob = new Blob([text], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "bulk_invite_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export async function fetchCreateNewUserPage(): Promise<CreateNewUserPage> {
  return apiRequest<CreateNewUserPage>("/college-admin/users/create-new-user/page");
}

export async function saveCreateNewUserDraft(payload: {
  step_key?: string;
  values: Record<string, unknown>;
}): Promise<CreateNewUserPage> {
  return apiRequest<CreateNewUserPage>("/college-admin/users/create-new-user/draft", {
    method: "PUT",
    body: payload,
  });
}

export async function validateCreateNewUser(values: Record<string, unknown>): Promise<{
  validation_checks: CreateNewUserValidationCheck[];
  review_lines: CreateNewUserReviewLine[];
}> {
  return apiRequest("/college-admin/users/create-new-user/validate", {
    method: "POST",
    body: { values },
  });
}

export async function submitCreateNewUser(values: Record<string, unknown>): Promise<CreateNewUserSubmitResult> {
  return apiRequest<CreateNewUserSubmitResult>("/college-admin/users/create-new-user/submit", {
    method: "POST",
    body: { values, finalize: true },
  });
}

export async function fetchUserDetailsPage(userId: string): Promise<UserDetailsPage> {
  const qs = new URLSearchParams({ user_id: userId });
  return apiRequest<UserDetailsPage>(`/college-admin/users/user-details/page?${qs.toString()}`);
}

export async function fetchEditUserInformationPage(userId: string): Promise<EditUserInformationPage> {
  const qs = new URLSearchParams({ user_id: userId });
  return apiRequest<EditUserInformationPage>(`/college-admin/users/edit-user-information/page?${qs.toString()}`);
}

export async function saveEditUserInformation(payload: {
  user_id: string;
  values: Record<string, unknown>;
}): Promise<EditUserInformationPage> {
  return apiRequest<EditUserInformationPage>("/college-admin/users/edit-user-information/save", {
    method: "PUT",
    body: payload,
  });
}

export async function revokeUserSessions(userId: string): Promise<{ revoked?: number }> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}/sessions/revoke`, {
    method: "POST",
    body: {},
  });
}

export async function resetUserAccess(userId: string): Promise<{ reset_token?: string; revoked_sessions?: number }> {
  return apiRequest(`/college-admin/users/${encodeURIComponent(userId)}/reset-access`, {
    method: "POST",
    body: {},
  });
}

export async function fetchUserManagementDashboardPage(params: {
  date_range?: string;
  role_filter?: string;
  department_id?: string;
} = {}): Promise<UserManagementDashboardPage> {
  const qs = new URLSearchParams();
  if (params.date_range) qs.set("date_range", params.date_range);
  if (params.role_filter) qs.set("role_filter", params.role_filter);
  if (params.department_id) qs.set("department_id", params.department_id);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<UserManagementDashboardPage>(
    `/college-admin/users/management-dashboard/page${suffix}`,
  );
}

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