import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AxeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 12L5.50001 20.5C5.10219 20.8978 4.56262 21.1213 4.00001 21.1213C3.4374 21.1213 2.89784 20.8978 2.50001 20.5C2.10219 20.1022 1.87869 19.5626 1.87869 19C1.87869 18.4374 2.10219 17.8978 2.50001 17.5L11 9"/>
      <path d="M15 13L9 7L13 3L19 9H22C21.7881 10.7831 20.9825 12.443 19.7128 13.7128C18.443 14.9825 16.7831 15.7881 15 16V13Z"/>

    </svg>
  );
}
