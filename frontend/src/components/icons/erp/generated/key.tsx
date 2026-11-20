import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function KeyIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15.5 7.5L17.8 9.8C17.9869 9.98323 18.2382 10.0859 18.5 10.0859C18.7618 10.0859 19.0131 9.98323 19.2 9.8L21.3 7.7C21.4832 7.51307 21.5859 7.26175 21.5859 7C21.5859 6.73825 21.4832 6.48693 21.3 6.3L19 4"/>
      <path d="M21 2L11.4 11.6"/>
      <path d="M2 15.5C2 16.9587 2.57946 18.3576 3.61091 19.3891C4.64236 20.4205 6.04131 21 7.5 21C8.95869 21 10.3576 20.4205 11.3891 19.3891C12.4205 18.3576 13 16.9587 13 15.5C13 14.0413 12.4205 12.6424 11.3891 11.6109C10.3576 10.5795 8.95869 10 7.5 10C6.04131 10 4.64236 10.5795 3.61091 11.6109C2.57946 12.6424 2 14.0413 2 15.5Z"/>

    </svg>
  );
}
