import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MicOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L22 22"/>
      <path d="M18.89 13.23C18.9622 12.824 18.999 12.4124 19 12V10"/>
      <path d="M5.00001 10V12C4.97966 13.3992 5.37913 14.7723 6.14684 15.9422C6.91456 17.1121 8.01529 18.0251 9.30696 18.5633C10.5986 19.1015 12.022 19.2402 13.3933 18.9616C14.7645 18.6829 16.0208 17.9997 17 17"/>
      <path d="M15 9.34048V5.00048C14.9959 4.32685 14.7653 3.67419 14.3452 3.1476C13.9251 2.62101 13.3399 2.25115 12.684 2.09757C12.0281 1.94398 11.3396 2.01562 10.7294 2.30095C10.1192 2.58628 9.62271 3.06868 9.32001 3.67048"/>
      <path d="M9 9V12C9.00052 12.593 9.17675 13.1725 9.50643 13.6653C9.83611 14.1582 10.3045 14.5423 10.8523 14.7691C11.4002 14.996 12.0029 15.0554 12.5845 14.9399C13.1661 14.8243 13.7005 14.539 14.12 14.12"/>
      <path d="M12 19V22"/>

    </svg>
  );
}
