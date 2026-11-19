"use client";

const ACCESS_KEY = "erp.access_token";
const TENANT_OVERRIDE_KEY = "erp.tenant_override_id";

let inMemoryAccessToken: string | null = null;

function canUseSessionStorage(): boolean {
  return typeof window !== "undefined" && typeof sessionStorage !== "undefined";
}

export function getAccessToken(): string | null {
  if (inMemoryAccessToken) {
    return inMemoryAccessToken;
  }
  if (!canUseSessionStorage()) {
    return null;
  }
  return sessionStorage.getItem(ACCESS_KEY);
}

export function setAccessToken(token: string): void {
  inMemoryAccessToken = token;
  if (canUseSessionStorage()) {
    sessionStorage.setItem(ACCESS_KEY, token);
  }
}

export function clearAccessToken(): void {
  inMemoryAccessToken = null;
  if (canUseSessionStorage()) {
    sessionStorage.removeItem(ACCESS_KEY);
  }
}

export function getTenantOverrideId(): string | null {
  if (!canUseSessionStorage()) {
    return null;
  }
  return sessionStorage.getItem(TENANT_OVERRIDE_KEY);
}

export function setTenantOverrideId(tenantId: string | null): void {
  if (!canUseSessionStorage()) {
    return;
  }
  if (tenantId) {
    sessionStorage.setItem(TENANT_OVERRIDE_KEY, tenantId);
  } else {
    sessionStorage.removeItem(TENANT_OVERRIDE_KEY);
  }
}