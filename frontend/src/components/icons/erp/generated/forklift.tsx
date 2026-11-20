import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ForkliftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 12H5C4.46957 12 3.96086 12.2107 3.58579 12.5858C3.21071 12.9609 3 13.4696 3 14V19"/>
      <path d="M11 19C11 19.5304 11.2107 20.0391 11.5858 20.4142C11.9609 20.7893 12.4696 21 13 21C13.5304 21 14.0391 20.7893 14.4142 20.4142C14.7893 20.0391 15 19.5304 15 19C15 18.4696 14.7893 17.9609 14.4142 17.5858C14.0391 17.2107 13.5304 17 13 17C12.4696 17 11.9609 17.2107 11.5858 17.5858C11.2107 17.9609 11 18.4696 11 19Z"/>
      <path d="M3 19C3 19.5304 3.21071 20.0391 3.58579 20.4142C3.96086 20.7893 4.46957 21 5 21C5.53043 21 6.03914 20.7893 6.41421 20.4142C6.78929 20.0391 7 19.5304 7 19C7 18.4696 6.78929 17.9609 6.41421 17.5858C6.03914 17.2107 5.53043 17 5 17C4.46957 17 3.96086 17.2107 3.58579 17.5858C3.21071 17.9609 3 18.4696 3 19Z"/>
      <path d="M8 19H11M16 2V19H22M6 12V7C6 5.9 6.9 5 8 5H11L16 10"/>

    </svg>
  );
}
