import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudHailIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3.99997 14.8988C3.25701 14.1397 2.69654 13.2215 2.36101 12.2137C2.02547 11.2059 1.92368 10.135 2.06333 9.08208C2.20299 8.02913 2.58043 7.02178 3.16707 6.13631C3.75371 5.25085 4.53416 4.51049 5.44931 3.97133C6.36445 3.43216 7.3903 3.10833 8.44914 3.02435C9.50798 2.94038 10.572 3.09846 11.5607 3.48664C12.5494 3.87481 13.4368 4.48289 14.1557 5.26481C14.8746 6.04674 15.4061 6.98201 15.71 7.99978H17.5C18.4655 7.99967 19.4054 8.3101 20.181 8.88522C20.9565 9.46033 21.5265 10.2696 21.8067 11.1936C22.087 12.1175 22.0627 13.1071 21.7373 14.0162C21.412 14.9252 20.8028 15.7055 20 16.2418"/>
      <path d="M16 14V16"/>
      <path d="M8 14V16"/>
      <path d="M16 20H16.01"/>
      <path d="M8 20H8.01"/>
      <path d="M12 16V18"/>
      <path d="M12 22H12.01"/>

    </svg>
  );
}
