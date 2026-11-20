import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReceiptCentIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 2V22L6 21L8 22L10 21L12 22L14 21L16 22L18 21L20 22V2L18 3L16 2L14 3L12 2L10 3L8 2L6 3L4 2Z"/>
      <path d="M12 6.5V17.5"/>
      <path d="M14.9999 9.4C14.4685 8.77864 13.7593 8.33507 12.9681 8.12905C12.1768 7.92303 11.3414 7.96446 10.5744 8.24774C9.80736 8.53102 9.14559 9.04256 8.67818 9.71344C8.21078 10.3843 7.96021 11.1823 7.96021 12C7.96021 12.8177 8.21078 13.6157 8.67818 14.2866C9.14559 14.9574 9.80736 15.469 10.5744 15.7523C11.3414 16.0355 12.1768 16.077 12.9681 15.8709C13.7593 15.6649 14.4685 15.2214 14.9999 14.6"/>

    </svg>
  );
}
