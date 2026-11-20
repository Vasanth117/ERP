import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BitcoinIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11.767 19.089C16.691 19.957 17.907 13.064 12.983 12.195M11.767 19.089L7.82737 18.394M11.767 19.089L11.421 21.059M7.82737 18.394L5.85999 18.047M7.82737 18.394L7.47999 20.364M7.82737 18.394L10.2586 4.60711M9.04398 11.501L12.984 12.195C17.908 13.064 19.124 6.16996 14.199 5.30196L14.198 5.30179M14.198 5.30179L10.2586 4.60711M14.198 5.30179L14.198 5.30196M14.198 5.30179L14.546 3.33196M10.2586 4.60711L8.28999 4.25996M10.2586 4.60711L10.606 2.63696"/>

    </svg>
  );
}
