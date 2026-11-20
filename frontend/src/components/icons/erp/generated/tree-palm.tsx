import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TreePalmIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13 8C13 5.24 10.54 3 7.5 3C4.46 3 2 5.24 2 8H4L5 7L6 8H10"/>
      <path d="M13 7.14014C14.0126 6.39149 15.2407 5.99147 16.5 6.00014C19.54 6.00014 22 8.24014 22 11.0001H19L18 10.0001L17 11.0001H14"/>
      <path d="M5.88997 9.71046C3.73997 11.8605 3.58997 15.1805 5.53997 17.1405L9.77997 12.8905L10.48 12.1905L11.19 11.4805L13.31 9.36046C11.36 7.40046 8.03997 7.56046 5.88997 9.71046Z"/>
      <path d="M11 15.5C11.5 18 10.83 20 10 22H14C16 16.5 13.5 10 13 8"/>

    </svg>
  );
}
