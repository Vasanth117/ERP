import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CogIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 20C14.1217 20 16.1566 19.1571 17.6569 17.6569C19.1571 16.1566 20 14.1217 20 12C20 9.87827 19.1571 7.84344 17.6569 6.34315C16.1566 4.84285 14.1217 4 12 4C9.87827 4 7.84344 4.84285 6.34315 6.34315C4.84285 7.84344 4 9.87827 4 12C4 14.1217 4.84285 16.1566 6.34315 17.6569C7.84344 19.1571 9.87827 20 12 20Z"/>
      <path d="M12 14C12.5304 14 13.0391 13.7893 13.4142 13.4142C13.7893 13.0391 14 12.5304 14 12C14 11.4696 13.7893 10.9609 13.4142 10.5858C13.0391 10.2107 12.5304 10 12 10C11.4696 10 10.9609 10.2107 10.5858 10.5858C10.2107 10.9609 10 11.4696 10 12C10 12.5304 10.2107 13.0391 10.5858 13.4142C10.9609 13.7893 11.4696 14 12 14Z"/>
      <path d="M12 2V4"/>
      <path d="M12 22V20"/>
      <path d="M17 20.6602L16 18.9302"/>
      <path d="M11 10.2698L7 3.33984"/>
      <path d="M20.66 17L18.93 16"/>
      <path d="M3.34003 7L5.07003 8"/>
      <path d="M14 12H22"/>
      <path d="M2 12H4"/>
      <path d="M20.66 7L18.93 8"/>
      <path d="M3.34003 17L5.07003 16"/>
      <path d="M17 3.33984L16 5.06984"/>
      <path d="M11 13.73L7 20.66"/>

    </svg>
  );
}
