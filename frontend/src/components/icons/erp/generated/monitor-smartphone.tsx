import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MonitorSmartphoneIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 8V6C18 5.46957 17.7893 4.96086 17.4142 4.58579C17.0391 4.21071 16.5304 4 16 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V13C2 13.5304 2.21071 14.0391 2.58579 14.4142C2.96086 14.7893 3.46957 15 4 15H12"/>
      <path d="M10 19V15.04V18.19"/>
      <path d="M7 19H12"/>
      <path d="M18 12H20C20.5304 12 21.0391 12.2107 21.4142 12.5858C21.7893 12.9609 22 13.4696 22 14V20C22 20.5304 21.7893 21.0391 21.4142 21.4142C21.0391 21.7893 20.5304 22 20 22H18C17.4696 22 16.9609 21.7893 16.5858 21.4142C16.2107 21.0391 16 20.5304 16 20V14C16 13.4696 16.2107 12.9609 16.5858 12.5858C16.9609 12.2107 17.4696 12 18 12Z"/>

    </svg>
  );
}
