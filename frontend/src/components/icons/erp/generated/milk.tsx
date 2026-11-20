import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MilkIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2H16"/>
      <path d="M9 2V4.789C8.99998 5.57879 8.76616 6.3509 8.328 7.008L7.672 7.992C7.23366 8.64939 6.99982 9.42187 7 10.212V20C7 20.5304 7.21071 21.0391 7.58579 21.4142C7.96086 21.7893 8.46957 22 9 22H15C15.5304 22 16.0391 21.7893 16.4142 21.4142C16.7893 21.0391 17 20.5304 17 20V10.211C17 9.42121 16.7662 8.6491 16.328 7.992L15.672 7.008C15.2337 6.35061 14.9998 5.57813 15 4.788V2"/>
      <path d="M7 15.0004C7.79177 14.6688 8.6416 14.498 9.5 14.498C10.3584 14.498 11.2082 14.6688 12 15.0004C12.7917 15.3321 13.6416 15.5029 14.5 15.5029C15.3584 15.5029 16.2083 15.3321 17 15.0004"/>

    </svg>
  );
}
