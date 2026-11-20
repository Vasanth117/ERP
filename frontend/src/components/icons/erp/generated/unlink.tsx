import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UnlinkIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.84 12.25L20.56 10.54H20.54C21.4606 9.58603 21.9651 8.30572 21.9426 6.98017C21.9201 5.65461 21.3725 4.39216 20.42 3.46999C19.4869 2.57019 18.2412 2.06738 16.945 2.06738C15.6488 2.06738 14.4031 2.57019 13.47 3.46999L11.75 5.17999"/>
      <path d="M5.17 11.75L3.46 13.46C2.53937 14.414 2.03492 15.6943 2.05742 17.0198C2.07992 18.3454 2.62752 19.6078 3.58 20.53C4.51305 21.4298 5.75876 21.9326 7.055 21.9326C8.35124 21.9326 9.59695 21.4298 10.53 20.53L12.24 18.82"/>
      <path d="M8 2V5"/>
      <path d="M2 8H5"/>
      <path d="M16 19V22"/>
      <path d="M19 16H22"/>

    </svg>
  );
}
