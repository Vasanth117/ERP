import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MessageSquareLockIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19 15V13C19 12.4696 18.7893 11.9609 18.4142 11.5858C18.0391 11.2107 17.5304 11 17 11C16.4696 11 15.9609 11.2107 15.5858 11.5858C15.2107 11.9609 15 12.4696 15 13V15"/>
      <path d="M9 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V8.5"/>
      <path d="M14 15H20C20.2652 15 20.5196 15.1054 20.7071 15.2929C20.8946 15.4804 21 15.7348 21 16V19C21 19.2652 20.8946 19.5196 20.7071 19.7071C20.5196 19.8946 20.2652 20 20 20H14C13.7348 20 13.4804 19.8946 13.2929 19.7071C13.1054 19.5196 13 19.2652 13 19V16C13 15.7348 13.1054 15.4804 13.2929 15.2929C13.4804 15.1054 13.7348 15 14 15Z"/>

    </svg>
  );
}
