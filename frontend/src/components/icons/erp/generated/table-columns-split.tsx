import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TableColumnsSplitIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 14V16"/>
      <path d="M14 20V22"/>
      <path d="M14 2V4"/>
      <path d="M14 8V10"/>
      <path d="M2 15H10"/>
      <path d="M2 3H8C8.53043 3 9.03914 3.21071 9.41421 3.58579C9.78929 3.96086 10 4.46957 10 5V19C10 19.5304 9.78929 20.0391 9.41421 20.4142C9.03914 20.7893 8.53043 21 8 21H2"/>
      <path d="M2 9H10"/>
      <path d="M22 15H18"/>
      <path d="M22 3H20C19.4696 3 18.9609 3.21071 18.5858 3.58579C18.2107 3.96086 18 4.46957 18 5V19C18 19.5304 18.2107 20.0391 18.5858 20.4142C18.9609 20.7893 19.4696 21 20 21H22"/>
      <path d="M22 9H18"/>
      <path d="M5 3V21"/>

    </svg>
  );
}
