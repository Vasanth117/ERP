import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="h-dvh overflow-hidden bg-[#eef2f6]">{children}</div>
  );
}