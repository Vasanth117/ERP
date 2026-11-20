import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SunIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 12C8 13.0609 8.42143 14.0783 9.17157 14.8284C9.92172 15.5786 10.9391 16 12 16C13.0609 16 14.0783 15.5786 14.8284 14.8284C15.5786 14.0783 16 13.0609 16 12C16 10.9391 15.5786 9.92172 14.8284 9.17157C14.0783 8.42143 13.0609 8 12 8C10.9391 8 9.92172 8.42143 9.17157 9.17157C8.42143 9.92172 8 10.9391 8 12Z"/>
      <path d="M12 2V4"/>
      <path d="M12 20V22"/>
      <path d="M4.92999 4.92969L6.33999 6.33969"/>
      <path d="M17.66 17.6602L19.07 19.0702"/>
      <path d="M2 12H4"/>
      <path d="M20 12H22"/>
      <path d="M6.33999 17.6602L4.92999 19.0702"/>
      <path d="M19.07 4.92969L17.66 6.33969"/>

    </svg>
  );
}
