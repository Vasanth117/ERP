import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WifiHighIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 20H12.01"/>
      <path d="M5 12.8591C6.86929 11.0268 9.38247 10.0005 12 10.0005C14.6175 10.0005 17.1307 11.0268 19 12.8591"/>
      <path d="M8.5 16.4288C9.43464 15.5127 10.6912 14.9995 12 14.9995C13.3088 14.9995 14.5654 15.5127 15.5 16.4288"/>

    </svg>
  );
}
