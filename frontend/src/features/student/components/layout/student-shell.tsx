import type { ReactNode } from "react";

import { StudentHeader } from "@/features/student/components/layout/student-header";
import { StudentSidebar } from "@/features/student/components/layout/student-sidebar";

export function StudentShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-white">
      <StudentSidebar />
      <div className="flex min-w-0 flex-1 flex-col bg-white">
        <StudentHeader />
        <main className="flex-1 overflow-auto bg-[#f8fafc] px-6 py-5 md:px-8 md:py-6">
          {children}
        </main>
      </div>
    </div>
  );
}