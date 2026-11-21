import { LoginPageChrome } from "@/components/auth/login-page-chrome";

export function LoginFormSkeleton() {
  return (
    <LoginPageChrome portal="default">
      <div className="space-y-5" aria-hidden>
        <div className="h-11 animate-pulse rounded-lg bg-[#eef2f9]" />
        <div className="h-11 animate-pulse rounded-lg bg-[#eef2f9]" />
        <div className="h-11 animate-pulse rounded-lg bg-[#eef2f9]" />
        <div className="h-11 animate-pulse rounded-lg bg-[#eef2f9]" />
      </div>
    </LoginPageChrome>
  );
}