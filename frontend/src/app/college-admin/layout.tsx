import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import { CollegeAdminAuthGate } from "@/features/college-admin/components/layout/college-admin-auth-gate";
import { CollegeAdminProviders } from "@/features/college-admin/components/layout/college-admin-providers";
import { CollegeAdminShell } from "@/features/college-admin/components/layout/college-admin-shell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-college-admin",
  display: "swap",
});

export default function CollegeAdminLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className={`${inter.className} ${inter.variable} text-[#172b45] antialiased`}
      data-college-admin-font=""
    >
      <CollegeAdminProviders>
        <CollegeAdminShell>
          <CollegeAdminAuthGate>{children}</CollegeAdminAuthGate>
        </CollegeAdminShell>
      </CollegeAdminProviders>
    </div>
  );
}