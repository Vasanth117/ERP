import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EuroIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 10H16"/>
      <path d="M4 14H13"/>
      <path d="M19 6.00003C17.5771 4.70768 15.7222 3.99427 13.8 4.00003C12.7625 4.01308 11.7378 4.23037 10.7843 4.63949C9.83083 5.0486 8.96727 5.64153 8.24296 6.38442C7.51864 7.1273 6.94776 8.00559 6.56291 8.96913C6.17806 9.93266 5.98678 10.9626 6 12C6 16.4 9.5 20 13.8 20C15.8 20 17.6 19.2 19 18"/>

    </svg>
  );
}
