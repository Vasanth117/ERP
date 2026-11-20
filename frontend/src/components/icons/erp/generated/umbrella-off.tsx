import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UmbrellaOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V3"/>
      <path d="M15.5 20.9998C15.3083 21.3882 14.9864 21.697 14.5904 21.8724C14.1943 22.0478 13.7493 22.0787 13.3329 21.9597C12.9164 21.8407 12.5549 21.5794 12.3113 21.2212C12.0678 20.8631 11.9576 20.4308 12 19.9998V11.9998H2C2.25786 9.44982 3.48497 7.09619 5.428 5.4248"/>
      <path d="M17.5 12.0001H22C21.8538 10.5162 21.3776 9.08371 20.6063 7.8076C19.835 6.53149 18.788 5.44403 17.5421 4.62482C16.2962 3.80562 14.8828 3.27541 13.4055 3.07302C11.9282 2.87062 10.4243 3.00116 9.004 3.45508"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
