import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SquareParkingOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3.59998 3.6C3.96924 3.22317 4.47244 3.00751 4.99998 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C20.9977 19.5296 20.7856 20.0366 20.41 20.41"/>
      <path d="M3 8.7002V19.0002C3 19.5306 3.21071 20.0393 3.58579 20.4144C3.96086 20.7895 4.46957 21.0002 5 21.0002H15.3"/>
      <path d="M2 2L22 22"/>
      <path d="M13 13C13.7956 13 14.5587 12.6839 15.1213 12.1213C15.6839 11.5587 16 10.7956 16 10C16 9.20435 15.6839 8.44129 15.1213 7.87868C14.5587 7.31607 13.7956 7 13 7H9V9"/>
      <path d="M9 17.0002V14.7002"/>

    </svg>
  );
}
