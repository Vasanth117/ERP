import type { ReactNode } from "react";

import { StudentPortalChrome } from "@/features/student/components/layout/student-portal-chrome";
import { StudentSidebar } from "@/features/student/components/layout/student-sidebar";
import { PORTAL_CONTENT_COLUMN, PORTAL_MAIN, PORTAL_SHELL } from "@/lib/portal/shell-styles";

/** Student shell matches college admin: sidebar + main column (no top search header). */
export function StudentShell({ children }: { children: ReactNode }) {
  return (
    <div className={PORTAL_SHELL}>
      <StudentSidebar />
      <div className={PORTAL_CONTENT_COLUMN}>
        <main className={PORTAL_MAIN}>
          <StudentPortalChrome>{children}</StudentPortalChrome>
        </main>
      </div>
    </div>
  );
}