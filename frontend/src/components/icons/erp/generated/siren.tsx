import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SirenIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 18V12C7 10.6739 7.52678 9.40215 8.46447 8.46447C9.40215 7.52678 10.6739 7 12 7C13.3261 7 14.5979 7.52678 15.5355 8.46447C16.4732 9.40215 17 10.6739 17 12V18"/>
      <path d="M5 21C5 21.2652 5.10536 21.5196 5.29289 21.7071C5.48043 21.8946 5.73478 22 6 22H18C18.2652 22 18.5196 21.8946 18.7071 21.7071C18.8946 21.5196 19 21.2652 19 21V20C19 19.4696 18.7893 18.9609 18.4142 18.5858C18.0391 18.2107 17.5304 18 17 18H7C6.46957 18 5.96086 18.2107 5.58579 18.5858C5.21071 18.9609 5 19.4696 5 20V21Z"/>
      <path d="M21 12H22"/>
      <path d="M18.5 4.5L18 5"/>
      <path d="M2 12H3"/>
      <path d="M12 2V3"/>
      <path d="M4.929 4.9292L5.636 5.6362"/>
      <path d="M12 12V18"/>

    </svg>
  );
}
