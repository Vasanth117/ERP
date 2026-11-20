import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Scale3DIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 7V18C5 18.2652 5.10536 18.5196 5.29289 18.7071C5.48043 18.8946 5.73478 19 6 19H17"/>
      <path d="M5.29303 18.707L11 13"/>
      <path d="M17 19C17 19.5304 17.2107 20.0391 17.5858 20.4142C17.9609 20.7893 18.4696 21 19 21C19.5304 21 20.0391 20.7893 20.4142 20.4142C20.7893 20.0391 21 19.5304 21 19C21 18.4696 20.7893 17.9609 20.4142 17.5858C20.0391 17.2107 19.5304 17 19 17C18.4696 17 17.9609 17.2107 17.5858 17.5858C17.2107 17.9609 17 18.4696 17 19Z"/>
      <path d="M3 5C3 5.53043 3.21071 6.03914 3.58579 6.41421C3.96086 6.78929 4.46957 7 5 7C5.53043 7 6.03914 6.78929 6.41421 6.41421C6.78929 6.03914 7 5.53043 7 5C7 4.46957 6.78929 3.96086 6.41421 3.58579C6.03914 3.21071 5.53043 3 5 3C4.46957 3 3.96086 3.21071 3.58579 3.58579C3.21071 3.96086 3 4.46957 3 5Z"/>

    </svg>
  );
}
