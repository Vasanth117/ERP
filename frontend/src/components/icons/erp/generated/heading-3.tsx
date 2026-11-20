import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading3Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 12H12"/>
      <path d="M4 18V6"/>
      <path d="M12 18V6"/>
      <path d="M17.5 10.5002C19.2 9.50019 21 10.5002 21 12.0002C21 12.5306 20.7893 13.0393 20.4142 13.4144C20.0391 13.7895 19.5304 14.0002 19 14.0002"/>
      <path d="M17 17.5C19 19 21 17.8 21 16C21 15.4696 20.7893 14.9609 20.4142 14.5858C20.0391 14.2107 19.5304 14 19 14"/>

    </svg>
  );
}
