import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PocketKnifeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <g clip-path="url(#clip0_364_858)">
      <path d="M3 2V3C3 4 5 4 5 5C5 6 3 6 3 7C3 8 5 8 5 9C5 10 3 10 3 11C3 12 5 12 5 13"/>
      <path d="M18 6H18.01"/>
      <path d="M6 18H6.01"/>
      <path d="M20.83 8.83027C21.2016 8.45863 21.4964 8.01743 21.6976 7.53186C21.8987 7.04628 22.0022 6.52585 22.0022 6.00027C22.0022 5.47469 21.8987 4.95426 21.6976 4.46869C21.4964 3.98311 21.2016 3.54191 20.83 3.17027C20.4584 2.79863 20.0172 2.50383 19.5316 2.3027C19.046 2.10157 18.5256 1.99805 18 1.99805C17.4744 1.99805 16.954 2.10157 16.4684 2.3027C15.9828 2.50383 15.5416 2.79863 15.17 3.17027L3.17 15.1703C2.41943 15.9208 1.99777 16.9388 1.99777 18.0003C1.99777 18.5259 2.10129 19.0463 2.30242 19.5319C2.50355 20.0174 2.79836 20.4586 3.17 20.8303C3.54164 21.2019 3.98284 21.4967 4.46841 21.6978C4.95398 21.899 5.47442 22.0025 6 22.0025C7.06145 22.0025 8.07943 21.5808 8.83 20.8303L20.83 8.83027Z"/>
      <path d="M18 11.66V22C19.0609 22 20.0783 21.5786 20.8284 20.8284C21.5786 20.0783 22 19.0609 22 18V6"/>
      </g>
      <defs>
      <clipPath id="clip0_364_858">
      <rect width="24" height="24"/>
      </clipPath>
      </defs>

    </svg>
  );
}
