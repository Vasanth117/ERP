import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CalendarOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4.2 4.2002C3.84843 4.35357 3.54839 4.6048 3.33562 4.92395C3.12286 5.24309 3.00636 5.61668 3 6.0002V20.0002C3 20.5306 3.21071 21.0393 3.58579 21.4144C3.96086 21.7895 4.46957 22.0002 5 22.0002H19C19.3847 21.9994 19.761 21.8876 20.0839 21.6783C20.4067 21.4691 20.6623 21.1711 20.82 20.8202"/>
      <path d="M21 15.5V6C21 5.46957 20.7893 4.96086 20.4142 4.58579C20.0391 4.21071 19.5304 4 19 4H9.5"/>
      <path d="M16 2V6"/>
      <path d="M3 10H10"/>
      <path d="M21 10H15.5"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
