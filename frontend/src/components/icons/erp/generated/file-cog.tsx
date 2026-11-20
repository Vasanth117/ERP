import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileCogIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3.19999 12.9L2.29999 12.5"/>
      <path d="M3.19999 15.1001L2.29999 15.5001"/>
      <path d="M4.677 21.5C5.0398 21.82 5.50627 21.9976 5.99 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V6.5"/>
      <path d="M4.9 11.2L4.5 10.3"/>
      <path d="M4.9 16.8L4.5 17.7001"/>
      <path d="M7.50001 10.3L7.10001 11.2"/>
      <path d="M7.50001 17.7001L7.10001 16.8"/>
      <path d="M9.69999 12.5L8.79999 12.9"/>
      <path d="M9.69999 15.5001L8.79999 15.1001"/>
      <path d="M3 14C3 14.7956 3.31607 15.5587 3.87868 16.1213C4.44129 16.6839 5.20435 17 6 17C6.79565 17 7.55871 16.6839 8.12132 16.1213C8.68393 15.5587 9 14.7956 9 14C9 13.2044 8.68393 12.4413 8.12132 11.8787C7.55871 11.3161 6.79565 11 6 11C5.20435 11 4.44129 11.3161 3.87868 11.8787C3.31607 12.4413 3 13.2044 3 14Z"/>

    </svg>
  );
}
