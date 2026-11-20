import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileKeyIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2Z"/>
      <path d="M8 16C8 16.5304 8.21071 17.0391 8.58579 17.4142C8.96086 17.7893 9.46957 18 10 18C10.5304 18 11.0391 17.7893 11.4142 17.4142C11.7893 17.0391 12 16.5304 12 16C12 15.4696 11.7893 14.9609 11.4142 14.5858C11.0391 14.2107 10.5304 14 10 14C9.46957 14 8.96086 14.2107 8.58579 14.5858C8.21071 14.9609 8 15.4696 8 16Z"/>
      <path d="M16 10L11.5 14.5"/>
      <path d="M15 11L16 12"/>

    </svg>
  );
}
