"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { LoginField } from "@/components/auth/login-field";
import { LoginPageChrome } from "@/components/auth/login-page-chrome";
import { LoginRoleTabs } from "@/components/auth/login-role-tabs";
import { LoginSubmitButton } from "@/components/auth/login-submit-button";
import { PasswordField } from "@/components/auth/password-field";
import { fetchCurrentUser, loginWithBff } from "@/features/auth/api";
import {
  createInstitutionLoginSchema,
  createLoginFormSchema,
  createPortalLoginSchema,
  type InstitutionLoginValues,
  type LoginFormValues,
  type PortalLoginValues,
} from "@/features/auth/schemas/login-schema";
import {
  normalizeLoginPayload,
  requiresTenantCodeForNext,
} from "@/lib/auth/login-normalize";
import {
  type LoginPortal,
  resolveLoginPortal,
  roleAllowedForPortal,
} from "@/lib/auth/login-portal";
import { homePathForRole } from "@/lib/auth/role-home";
import { setAccessToken } from "@/lib/auth/token-store";

type PerformanceMode = "student" | "parent";

const emptyInstitution = { email: "", password: "", tenant_code: "" };
const emptyPortal = { identifier: "", password: "" };

function InstitutionLoginForm({
  nextPath,
  portal,
}: {
  nextPath: string;
  portal: LoginPortal;
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const schema = useMemo(() => createInstitutionLoginSchema(), []);

  const form = useForm<InstitutionLoginValues>({
    resolver: zodResolver(schema),
    defaultValues: emptyInstitution,
  });

  async function onSubmit(values: InstitutionLoginValues) {
    setSubmitting(true);
    try {
      const payload = normalizeLoginPayload({
        email: values.email,
        password: values.password,
        tenant_code: values.tenant_code,
      });
      const { access_token } = await loginWithBff(payload);
      setAccessToken(access_token);
      const me = await fetchCurrentUser();
      if (!roleAllowedForPortal(me.role, portal, "student")) {
        toast.error("This account is not authorized for Institution Management.");
        return;
      }
      toast.success(`Welcome, ${me.full_name}`);
      router.replace(nextPath);
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign in");
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
    <LoginPageChrome portal={portal}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <LoginField
          id="email"
          label="Email"
          type="email"
          placeholder="Enter your email"
          autoComplete="email"
          disabled={submitting}
          error={errors.email?.message}
          {...register("email")}
        />
        <PasswordField
          id="password"
          label="Password"
          placeholder="Enter your password"
          disabled={submitting}
          error={errors.password?.message}
          register={register("password")}
        />
        <LoginField
          id="tenant_code"
          label="College code"
          placeholder="Enter college code"
          autoComplete="organization"
          disabled={submitting}
          error={errors.tenant_code?.message}
          {...register("tenant_code")}
        />
        <LoginSubmitButton disabled={submitting}>
          {submitting ? "Signing in…" : "Sign In"}
        </LoginSubmitButton>
      </form>
    </LoginPageChrome>
  );
}

function StudentPerformanceLoginForm({
  nextPath,
  portal,
}: {
  nextPath: string;
  portal: LoginPortal;
}) {
  const router = useRouter();
  const [mode, setMode] = useState<PerformanceMode>("student");
  const [submitting, setSubmitting] = useState(false);
  const schema = useMemo(() => createPortalLoginSchema(), []);

  const form = useForm<PortalLoginValues>({
    resolver: zodResolver(schema),
    defaultValues: emptyPortal,
  });

  function switchMode(next: PerformanceMode) {
    setMode(next);
    form.reset(emptyPortal);
  }

  async function onSubmit(values: PortalLoginValues) {
    setSubmitting(true);
    try {
      const payload = normalizeLoginPayload({
        email: values.identifier,
        password: values.password,
      });
      const { access_token } = await loginWithBff(payload);
      setAccessToken(access_token);
      const me = await fetchCurrentUser();
      if (!roleAllowedForPortal(me.role, portal, mode)) {
        const label = mode === "student" ? "student" : "parent";
        toast.error(`This account is not a ${label} portal user.`);
        return;
      }
      toast.success(`Welcome, ${me.full_name}`);
      const destination =
        me.role === "parent"
          ? "/under-construction?module=parent"
          : nextPath;
      router.replace(destination);
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign in");
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
    <LoginPageChrome portal={portal}>
      <LoginRoleTabs value={mode} onChange={switchMode} />
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
        <LoginField
          id="identifier"
          label={mode === "student" ? "Student ID" : "Parent ID"}
          placeholder={
            mode === "student" ? "Enter student ID" : "Enter parent ID"
          }
          autoComplete="username"
          disabled={submitting}
          error={errors.identifier?.message}
          {...register("identifier")}
        />
        <PasswordField
          id="password"
          label="Password"
          placeholder="Enter your password"
          disabled={submitting}
          error={errors.password?.message}
          register={register("password")}
        />
        <LoginSubmitButton disabled={submitting}>
          {submitting ? "Signing in…" : "Sign In"}
        </LoginSubmitButton>
      </form>
    </LoginPageChrome>
  );
}

function DefaultLoginForm({
  nextPath,
  portal,
}: {
  nextPath: string;
  portal: LoginPortal;
}) {
  const router = useRouter();
  const requireTenantCode = requiresTenantCodeForNext(nextPath);
  const loginSchema = useMemo(
    () => createLoginFormSchema(requireTenantCode),
    [requireTenantCode],
  );
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", tenant_code: "" },
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
      const me = await fetchCurrentUser();
      toast.success(`Welcome, ${me.full_name}`);
      const fallback = homePathForRole(me.role);
      const target =
        nextPath === "/dashboard" || !nextPath.startsWith("/")
          ? fallback
          : nextPath;
      router.replace(target);
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not sign in");
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
    <LoginPageChrome portal={portal}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <LoginField
          id="email"
          label="Email"
          type="email"
          placeholder="Enter your email"
          autoComplete="email"
          disabled={submitting}
          error={errors.email?.message}
          {...register("email")}
        />
        <PasswordField
          id="password"
          label="Password"
          placeholder="Enter your password"
          disabled={submitting}
          error={errors.password?.message}
          register={register("password")}
        />
        <LoginField
          id="tenant_code"
          label={
            requireTenantCode ? "College code" : "College code (optional)"
          }
          placeholder="Enter college code"
          autoComplete="organization"
          disabled={submitting}
          error={errors.tenant_code?.message}
          {...register("tenant_code")}
        />
        <LoginSubmitButton disabled={submitting}>
          {submitting ? "Signing in…" : "Sign In"}
        </LoginSubmitButton>
      </form>
    </LoginPageChrome>
  );
}

export function LoginForm() {
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") ?? "/";
  const portal = resolveLoginPortal(
    searchParams.get("portal"),
    nextPath,
  );

  if (portal === "institution") {
    return (
      <InstitutionLoginForm
        nextPath={
          nextPath.startsWith("/college-admin")
            ? nextPath
            : "/college-admin/dashboard"
        }
        portal={portal}
      />
    );
  }

  if (portal === "student-performance" || inferStudentPortal(nextPath)) {
    return (
      <StudentPerformanceLoginForm
        nextPath={
          nextPath.startsWith("/student") ? nextPath : "/student/dashboard"
        }
        portal="student-performance"
      />
    );
  }

  if (portal === "default" && (nextPath === "/" || nextPath === "")) {
    return <DefaultLoginForm nextPath="/" portal={portal} />;
  }

  return <DefaultLoginForm nextPath={nextPath} portal={portal} />;
}

function inferStudentPortal(nextPath: string): boolean {
  return nextPath === "/student" || nextPath.startsWith("/student/");
}