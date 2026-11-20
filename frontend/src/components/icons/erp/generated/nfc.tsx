import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function NfcIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 8.31982C6.6392 9.44097 6.97535 10.7093 6.97535 11.9998C6.97535 13.2904 6.6392 14.5587 6 15.6798"/>
      <path d="M9.45999 6.20996C10.459 7.97615 10.9841 9.97079 10.9841 12C10.9841 14.0291 10.459 16.0238 9.45999 17.79"/>
      <path d="M12.91 4.1001C14.2876 6.50473 15.0132 9.22749 15.0149 11.9988C15.0167 14.77 14.2945 17.4937 12.92 19.9001"/>
      <path d="M16.37 2C18.1098 5.04561 19.025 8.49246 19.025 12C19.025 15.5075 18.1098 18.9544 16.37 22"/>

    </svg>
  );
}
