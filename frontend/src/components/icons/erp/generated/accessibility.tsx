import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AccessibilityIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 4C15 4.26522 15.1054 4.51957 15.2929 4.70711C15.4804 4.89464 15.7348 5 16 5C16.2652 5 16.5196 4.89464 16.7071 4.70711C16.8946 4.51957 17 4.26522 17 4C17 3.73478 16.8946 3.48043 16.7071 3.29289C16.5196 3.10536 16.2652 3 16 3C15.7348 3 15.4804 3.10536 15.2929 3.29289C15.1054 3.48043 15 3.73478 15 4Z"/>
      <path d="M18 19L19 12L13 13"/>
      <path d="M5 8L8 5L13.5 8L11.14 11.5"/>
      <path d="M4.24 14.5C3.95784 15.4231 3.94888 16.4081 4.21422 17.3361C4.47955 18.2641 5.00782 19.0955 5.73528 19.73C6.46273 20.3644 7.35826 20.7746 8.31376 20.9113C9.26927 21.0479 10.2439 20.9051 11.12 20.5"/>
      <path d="M13.76 17.5C14.0422 16.5769 14.0511 15.5919 13.7858 14.6639C13.5205 13.7358 12.9922 12.9044 12.2647 12.27C11.5373 11.6356 10.6417 11.2253 9.68624 11.0887C8.73073 10.952 7.7561 11.0949 6.88 11.5"/>

    </svg>
  );
}
