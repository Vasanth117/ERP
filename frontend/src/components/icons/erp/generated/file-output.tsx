import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileOutputIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 2V6C14 6.53043 14.2107 7.03914 14.5858 7.41421C14.9609 7.78929 15.4696 8 16 8H20"/>
      <path d="M4 7V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2"/>
      <path d="M4.06299 20.999C4.25885 21.3459 4.55385 21.6264 4.91018 21.8046C5.26651 21.9828 5.66794 22.0505 6.06299 21.999L18 22C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H5.99999"/>
      <path d="M5 11L2 14"/>
      <path d="M5 17L2 14H12"/>

    </svg>
  );
}
