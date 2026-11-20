import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WarehouseIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 8.3499V19.9999C22 20.5303 21.7893 21.039 21.4142 21.4141C21.0391 21.7892 20.5304 21.9999 20 21.9999H4C3.46957 21.9999 2.96086 21.7892 2.58579 21.4141C2.21071 21.039 2 20.5303 2 19.9999V8.3499C2.00161 7.95104 2.12244 7.56178 2.34696 7.23212C2.57149 6.90247 2.88945 6.64747 3.26 6.4999L11.26 3.2999C11.7352 3.11065 12.2648 3.11065 12.74 3.2999L20.74 6.4999C21.1106 6.64747 21.4285 6.90247 21.653 7.23212C21.8776 7.56178 21.9984 7.95104 22 8.3499Z"/>
      <path d="M6 18H18"/>
      <path d="M6 14H18"/>
      <path d="M6 10H18V22H6V10Z"/>

    </svg>
  );
}
