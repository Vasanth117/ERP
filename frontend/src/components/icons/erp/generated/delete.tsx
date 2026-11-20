import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DeleteIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 5C9.50309 5.00003 9.02397 5.18504 8.656 5.519L2.328 11.259C2.22472 11.3527 2.14219 11.467 2.08572 11.5946C2.02924 11.7221 2.00006 11.86 2.00006 11.9995C2.00006 12.139 2.02924 12.2769 2.08572 12.4044C2.14219 12.532 2.22472 12.6463 2.328 12.74L8.656 18.481C9.02397 18.815 9.50309 19 10 19H20C20.5304 19 21.0391 18.7893 21.4142 18.4142C21.7893 18.0391 22 17.5304 22 17V7C22 6.46957 21.7893 5.96086 21.4142 5.58579C21.0391 5.21071 20.5304 5 20 5H10Z"/>
      <path d="M12 9L18 15"/>
      <path d="M18 9L12 15"/>

    </svg>
  );
}
