import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReceiptEuroIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 12H13"/>
      <path d="M16 9.49998C15.4685 8.87861 14.7594 8.43505 13.9681 8.22903C13.1769 8.02301 12.3414 8.06443 11.5744 8.34771C10.8074 8.631 10.1456 9.14253 9.67825 9.81342C9.21084 10.4843 8.96027 11.2823 8.96027 12.1C8.96027 12.9176 9.21084 13.7156 9.67825 14.3865C10.1456 15.0574 10.8074 15.569 11.5744 15.8522C12.3414 16.1355 13.1769 16.1769 13.9681 15.9709C14.7594 15.7649 15.4685 15.3213 16 14.7"/>

    </svg>
  );
}
