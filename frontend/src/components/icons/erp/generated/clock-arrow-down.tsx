import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ClockArrowDownIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-6 shrink-0", className)}
      aria-hidden
      {...props}
    >
      <path d="M12.338 21.9938C10.2945 22.0628 8.27903 21.5038 6.56309 20.392C4.84714 19.2802 3.51322 17.6692 2.74108 15.7759C1.96895 13.8827 1.7957 11.7983 2.24469 9.80358C2.69367 7.80886 3.74332 5.9997 5.25218 4.6199C6.76103 3.2401 8.65659 2.35597 10.6834 2.08665C12.7102 1.81733 14.7709 2.17577 16.5877 3.11366C18.4045 4.05155 19.8902 5.52382 20.8445 7.33208C21.7988 9.14033 22.1759 11.1977 21.925 13.2268"/>
      <path d="M12 6V12L14 13"/>
      <path d="M14 18L18 22L22 18"/>
      <path d="M18 14V22"/>

    </svg>
  );
}
