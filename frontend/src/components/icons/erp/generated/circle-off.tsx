import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8.34998 2.69014C10.1606 1.98297 12.1381 1.81882 14.0405 2.21778C15.943 2.61675 17.6879 3.56153 19.0618 4.93655C20.4358 6.31157 21.3792 8.05722 21.7767 9.95997C22.1742 11.8627 22.0085 13.8401 21.3 15.6501"/>
      <path d="M19.08 19.0799C18.1502 20.0097 17.0465 20.7472 15.8317 21.2504C14.6169 21.7536 13.3149 22.0126 12 22.0126C10.6851 22.0126 9.38312 21.7536 8.16833 21.2504C6.95354 20.7472 5.84976 20.0097 4.92 19.0799C3.99024 18.1502 3.25271 17.0464 2.74953 15.8316C2.24635 14.6168 1.98737 13.3148 1.98737 11.9999C1.98737 10.685 2.24635 9.38304 2.74953 8.16825C3.25271 6.95346 3.99024 5.84968 4.92 4.91992"/>

    </svg>
  );
}
