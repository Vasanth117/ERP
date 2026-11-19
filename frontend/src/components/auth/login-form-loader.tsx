"use client";

import dynamic from "next/dynamic";

import { LoginFormSkeleton } from "@/components/auth/login-form-skeleton";

const LoginForm = dynamic(
  () =>
    import("@/components/auth/login-form").then((module) => module.LoginForm),
  {
    ssr: false,
    loading: () => <LoginFormSkeleton />,
  },
);

export function LoginFormLoader() {
  return <LoginForm />;
}