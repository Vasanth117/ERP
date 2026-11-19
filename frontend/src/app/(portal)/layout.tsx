import type { ReactNode } from "react";

import { AppHeader } from "@/components/layout/app-header";

export default function PortalLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />
      <main className="flex-1 p-4 md:p-6">{children}</main>
    </div>
  );
}