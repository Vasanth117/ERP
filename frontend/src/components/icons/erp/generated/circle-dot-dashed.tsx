import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleDotDashedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <g clip-path="url(#clip0_363_796)">
      <path d="M10.1 2.17956C11.3548 1.93494 12.6451 1.93494 13.9 2.17956"/>
      <path d="M17.6 3.70996C18.6622 4.42822 19.5757 5.34503 20.29 6.40996"/>
      <path d="M21.82 10.0996C22.0646 11.3545 22.0646 12.6448 21.82 13.8996"/>
      <path d="M20.29 17.5996C19.5718 18.6619 18.655 19.5753 17.59 20.2896"/>
      <path d="M13.9 21.8203C12.6451 22.0647 11.3549 22.0647 10.1 21.8203"/>
      <path d="M6.40002 20.2898C5.33775 19.5716 4.42433 18.6548 3.71002 17.5898"/>
      <path d="M2.17999 13.8996C1.93537 12.6448 1.93537 11.3545 2.17999 10.0996"/>
      <path d="M3.71002 6.39996C4.42828 5.33769 5.34509 4.42427 6.41002 3.70996"/>
      <path d="M11 12C11 12.2652 11.1054 12.5196 11.2929 12.7071C11.4804 12.8946 11.7348 13 12 13C12.2652 13 12.5196 12.8946 12.7071 12.7071C12.8946 12.5196 13 12.2652 13 12C13 11.7348 12.8946 11.4804 12.7071 11.2929C12.5196 11.1054 12.2652 11 12 11C11.7348 11 11.4804 11.1054 11.2929 11.2929C11.1054 11.4804 11 11.7348 11 12Z"/>
      </g>
      <defs>
      <clipPath id="clip0_363_796">
      <rect width="24" height="24"/>
      </clipPath>
      </defs>

    </svg>
  );
}
