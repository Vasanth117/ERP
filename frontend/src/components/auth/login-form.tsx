"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginWithBff } from "@/features/auth/api";
import {
  createLoginFormSchema,
  type LoginFormValues,
} from "@/features/auth/schemas/login-schema";
import {
  normalizeLoginPayload,
  requiresTenantCodeForNext,
} from "@/lib/auth/login-normalize";
import { getDevLoginDefaults } from "@/lib/auth/dev-login-defaults";
import { setAccessToken } from "@/lib/auth/token-store";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") ?? "/dashboard";
  const requireTenantCode = requiresTenantCodeForNext(nextPath);
  const loginSchema = useMemo(
    () => createLoginFormSchema(requireTenantCode),
    [requireTenantCode],
  );
  const [submitting, setSubmitting] = useState(false);
  const devDefaults = useMemo(() => getDevLoginDefaults(), []);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: devDefaults.email,
      password: devDefaults.password,
      tenant_code: devDefaults.tenant_code,
    },
  });

  async function onSubmit(values: LoginFormValues) {
    setSubmitting(true);
    try {
      const { access_token } = await loginWithBff(
        normalizeLoginPayload({
          email: values.email,
          password: values.password,
          tenant_code: values.tenant_code,
        }),
      );
      setAccessToken(access_token);
      toast.success("Signed in");
      router.replace(nextPath.startsWith("/") ? nextPath : "/dashboard");
      router.refresh();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not sign in";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  }

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = form;

  return (
    <Card className="w-full max-w-md border-border/80 shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">College ERP</CardTitle>
        <CardDescription>
          Sign in with your institutional email. College users: enter your
          college code. Platform operators can leave college code blank.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              disabled={submitting}
              suppressHydrationWarning
              {...register("email")}
            />
            {errors.email ? (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              disabled={submitting}
              suppressHydrationWarning
              {...register("password")}
            />
            {errors.password ? (
              <p className="text-sm text-destructive">
                {errors.password.message}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="tenant_code">
              {requireTenantCode
                ? "College code"
                : "College code (optional)"}
            </Label>
            <Input
              id="tenant_code"
              type="text"
              autoComplete="organization"
              placeholder="e.g. DEMO-COLLEGE"
              disabled={submitting}
              suppressHydrationWarning
              {...register("tenant_code")}
            />
            {errors.tenant_code ? (
              <p className="text-sm text-destructive">
                {errors.tenant_code.message}
              </p>
            ) : null}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={submitting}
            suppressHydrationWarning
          >
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}