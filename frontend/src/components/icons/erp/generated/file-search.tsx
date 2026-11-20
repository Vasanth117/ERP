import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileSearchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4.268 21C4.44311 21.3033 4.69479 21.5553 4.99786 21.7308C5.30094 21.9063 5.64478 21.9991 5.995 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V7"/>
      <path d="M9 18L7.5 16.5"/>
      <path d="M2 14C2 14.7956 2.31607 15.5587 2.87868 16.1213C3.44129 16.6839 4.20435 17 5 17C5.79565 17 6.55871 16.6839 7.12132 16.1213C7.68393 15.5587 8 14.7956 8 14C8 13.2044 7.68393 12.4413 7.12132 11.8787C6.55871 11.3161 5.79565 11 5 11C4.20435 11 3.44129 11.3161 2.87868 11.8787C2.31607 12.4413 2 13.2044 2 14Z"/>

    </svg>
  );
}
