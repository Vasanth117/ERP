import { z } from "zod";

const passwordField = z
  .string()
  .trim()
  .min(1, "Password is required")
  .max(128);

const tenantCodeRequired = z
  .string()
  .trim()
  .min(1, "College code is required for college sign-in");

const tenantCodeOptional = z.string().trim().optional();

const emailField = z
  .string()
  .trim()
  .min(1, "Email is required")
  .email("Enter a valid email");

const institutionalIdField = z
  .string()
  .trim()
  .min(1, "Id is required")
  .max(64);

export function createInstitutionLoginSchema() {
  return z.object({
    email: emailField,
    password: passwordField,
    tenant_code: tenantCodeRequired,
  });
}

export function createPortalLoginSchema() {
  return z.object({
    identifier: institutionalIdField,
    password: passwordField,
  });
}

export function createLoginFormSchema(requireTenantCode: boolean) {
  return z.object({
    email: emailField,
    password: passwordField,
    tenant_code: requireTenantCode ? tenantCodeRequired : tenantCodeOptional,
  });
}

export type InstitutionLoginValues = z.infer<
  ReturnType<typeof createInstitutionLoginSchema>
>;
export type PortalLoginValues = z.infer<ReturnType<typeof createPortalLoginSchema>>;
export type LoginFormValues = z.infer<
  ReturnType<typeof createLoginFormSchema>
>;

export const loginFormSchema = createLoginFormSchema(false);