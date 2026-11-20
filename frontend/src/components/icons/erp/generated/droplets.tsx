import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DropletsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 16.2998C9.2 16.2998 11 14.4698 11 12.2498C11 11.0898 10.43 9.9898 9.29 9.0598C8.15 8.1298 7.29 6.7498 7 5.2998C6.71 6.7498 5.86 8.1398 4.71 9.0598C3.56 9.9798 3 11.0998 3 12.2498C3 14.4698 4.8 16.2998 7 16.2998Z"/>
      <path d="M12.56 6.59953C13.2478 5.50066 13.7353 4.28858 14 3.01953C14.5 5.51953 16 7.91953 18 9.51953C20 11.1195 21 13.0195 21 15.0195C21.0057 16.4018 20.6009 17.7547 19.8368 18.9066C19.0727 20.0586 17.9838 20.9577 16.7081 21.49C15.4324 22.0224 14.0274 22.1639 12.6712 21.8968C11.3149 21.6297 10.0685 20.9659 9.09 19.9895"/>

    </svg>
  );
}
