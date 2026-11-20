import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import { StudentAuthGate } from "@/features/student/components/layout/student-auth-gate";
import { StudentShell } from "@/features/student/components/layout/student-shell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-student-portal",
  display: "swap",
});

export default function StudentLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className={`${inter.className} ${inter.variable} text-[#172b45] antialiased`}
      data-student-portal=""
    >
      <StudentShell>
        <StudentAuthGate>{children}</StudentAuthGate>
      </StudentShell>
    </div>
  );
}