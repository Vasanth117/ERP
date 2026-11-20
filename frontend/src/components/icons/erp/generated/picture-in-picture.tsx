import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PictureInPictureIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 9.5H8V4.5M8 9.5L2 3.5M21 9.5V6.5C21 5.34 20.16 4.5 19 4.5H12M3 13.5V15.5C3 16.55 3.95 17.5 5 17.5H8"/>
      <path d="M14 13.5H20C20.5304 13.5 21.0391 13.7107 21.4142 14.0858C21.7893 14.4609 22 14.9696 22 15.5V18.5C22 19.0304 21.7893 19.5391 21.4142 19.9142C21.0391 20.2893 20.5304 20.5 20 20.5H14C13.4696 20.5 12.9609 20.2893 12.5858 19.9142C12.2107 19.5391 12 19.0304 12 18.5V15.5C12 14.9696 12.2107 14.4609 12.5858 14.0858C12.9609 13.7107 13.4696 13.5 14 13.5Z"/>

    </svg>
  );
}
