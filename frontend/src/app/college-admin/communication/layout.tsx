import type { ReactNode } from "react";

import { CommunicationModuleChrome } from "@/features/college-admin/components/layout/communication-module-chrome";

export default function CommunicationLayout({ children }: { children: ReactNode }) {
  return <CommunicationModuleChrome>{children}</CommunicationModuleChrome>;
}