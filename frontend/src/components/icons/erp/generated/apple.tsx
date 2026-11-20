import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AppleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 20.94C13.5 20.94 14.75 22 16 22C19 22 22 14 22 9.77995C21.9659 8.48468 21.4212 7.25538 20.4846 6.36C19.548 5.46462 18.2955 4.97575 17 4.99995C14.78 4.99995 13 6.43995 12 6.99995C11 6.43995 9.22 4.99995 7 4.99995C5.70375 4.97311 4.4497 5.4611 3.51253 6.35703C2.57536 7.25297 2.03147 8.48381 2 9.77995C2 14 5 22 8 22C9.25 22 10.5 20.94 12 20.94Z"/>
      <path d="M10 2C11 2.5 12 4 12 7"/>

    </svg>
  );
}
