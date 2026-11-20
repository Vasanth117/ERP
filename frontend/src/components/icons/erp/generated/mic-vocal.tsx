import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MicVocalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 7.60059L5.00603 15.7906C4.86499 15.9833 4.79754 16.22 4.81588 16.4581C4.83422 16.6962 4.93714 16.9198 5.10603 17.0886L5.92303 17.9066C6.09438 18.0777 6.32202 18.1809 6.56369 18.1969C6.80535 18.2129 7.04461 18.1407 7.23703 17.9936L15.09 11.9996"/>
      <path d="M16.5 21.174C15.5 20.5 14.372 20 13 20C10.942 20 9.07198 22.356 6.99998 22C4.92798 21.644 4.22498 18.631 5.49998 17.5"/>
      <path d="M11 7C11 8.32608 11.5268 9.59785 12.4645 10.5355C13.4021 11.4732 14.6739 12 16 12C17.3261 12 18.5979 11.4732 19.5355 10.5355C20.4732 9.59785 21 8.32608 21 7C21 5.67392 20.4732 4.40215 19.5355 3.46447C18.5979 2.52678 17.3261 2 16 2C14.6739 2 13.4021 2.52678 12.4645 3.46447C11.5268 4.40215 11 5.67392 11 7Z"/>

    </svg>
  );
}
