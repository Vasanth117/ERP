import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import { underConstructionPageGradient } from "@/features/under-construction/constants";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

/**
 * Full viewport shell (Figma 342:214 — 1440×1024). `fixed` escapes any in-flow width quirks.
 * @see FIGMA_TO_FRONTEND_IMPLEMENTATION_GUIDE.md §6–8
 */
export default function UnderConstructionLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      className={`${inter.className} fixed inset-0 z-0 h-dvh w-full min-w-0 overflow-hidden overscroll-none`}
      style={{ backgroundImage: underConstructionPageGradient }}
    >
      <div className="relative h-full w-full min-w-0">{children}</div>
    </div>
  );
}