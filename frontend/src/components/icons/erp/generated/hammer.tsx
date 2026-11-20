import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HammerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15.0001 12L6.62706 20.373C6.22923 20.7708 5.68967 20.9943 5.12706 20.9943C4.56445 20.9943 4.02488 20.7708 3.62706 20.373C3.22923 19.9752 3.00574 19.4356 3.00574 18.873C3.00574 18.3104 3.22923 17.7708 3.62706 17.373L12.0001 9"/>
      <path d="M18 15L22 11"/>
      <path d="M21.5 11.5L19.586 9.58596C19.2109 9.21098 19.0001 8.70235 19 8.17196V6.99996L16.74 4.73996C15.6245 3.62515 14.115 2.99432 12.538 2.98396L9 2.95996L9.92 3.77996C10.5735 4.35935 11.0967 5.07066 11.4552 5.867C11.8137 6.66335 11.9994 7.52663 12 8.39996V9.99996L14 12H15.172C15.7024 12.0001 16.211 12.2109 16.586 12.586L18.5 14.5"/>

    </svg>
  );
}
