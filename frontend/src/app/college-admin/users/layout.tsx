import type { ReactNode } from "react";

import { UsersModuleChrome } from "@/features/college-admin/components/layout/users-module-chrome";

export default function UsersLayout({ children }: { children: ReactNode }) {
  return <UsersModuleChrome>{children}</UsersModuleChrome>;
}