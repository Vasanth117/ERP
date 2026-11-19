import { z } from "zod";

const emailField = z
  .string()
  .trim()
  .min(1, "Email is required")
  .email("Enter a valid email");

const passwordField = z
  .string()
  .trim()
  .min(1, "Password is required")
  .max(128);

const tenantCodeOptional = z.string().trim().optional();

const tenantCodeRequired = z
  .string()
  .trim()
  .min(1, "College code is required for college sign-in");

export function createLoginFormSchema(requireTenantCode: boolean) {
  return z.object({
    email: emailField,
    password: passwordField,
    tenant_code: requireTenantCode ? tenantCodeRequired : tenantCodeOptional,
  });
}

export type LoginFormValues = z.infer<
  ReturnType<typeof createLoginFormSchema>
>;

/** Default schema when tenant code is optional (platform or unknown `next`). */
export const loginFormSchema = createLoginFormSchema(false);