import type { Metadata } from "next";
import { Suspense } from "react";

import { UnderConstructionView } from "@/features/under-construction/under-construction-view";

export const metadata: Metadata = {
  title: "Page Under Construction — College ERP",
  description:
    "This module workspace is not available yet. Return to the main module launcher.",
};

export default function UnderConstructionPage() {
  return (
    <Suspense>
      <UnderConstructionView />
    </Suspense>
  );
}