import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SunDimIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 4H12.01"/>
      <path d="M20 12H20.01"/>
      <path d="M12 20H12.01"/>
      <path d="M4 12H4.01"/>
      <path d="M17.657 6.34277H17.667"/>
      <path d="M17.657 17.6572H17.667"/>
      <path d="M6.34299 17.6572H6.35299"/>
      <path d="M6.34299 6.34277H6.35299"/>

    </svg>
  );
}
