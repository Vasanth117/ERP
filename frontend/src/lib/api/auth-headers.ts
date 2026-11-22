import {
  getAccessToken,
  getTenantOverrideId,
} from "@/lib/auth/token-store";
import { isCollegeAdminDemoViewActive } from "@/lib/demo-mode/college-admin-demo-mode";

/** Attach bearer token, optional platform tenant override, and college-admin demo view header. */
export function applyAuthHeaders(headers: Headers): void {
  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const tenantId = getTenantOverrideId();
  if (tenantId) {
    headers.set("X-Tenant-Id", tenantId);
  }
  if (isCollegeAdminDemoViewActive()) {
    headers.set("X-Demo-College-View", "1");
  }
}