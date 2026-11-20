import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BluetoothOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 17L12 22V12L7 17"/>
      <path d="M2 2L22 22"/>
      <path d="M14.5 9.5L17 7L12 2V6.5"/>

    </svg>
  );
}
