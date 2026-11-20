import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShoppingBasketIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 11L14 20"/>
      <path d="M19 11L15 4"/>
      <path d="M2 11H22"/>
      <path d="M3.5 11L5.1 18.4C5.1935 18.8586 5.44485 19.2698 5.81028 19.5621C6.17572 19.8545 6.63211 20.0094 7.1 20H16.9C17.3679 20.0094 17.8243 19.8545 18.1897 19.5621C18.5552 19.2698 18.8065 18.8586 18.9 18.4L20.6 11"/>
      <path d="M4.5 15.5H19.5"/>
      <path d="M5 11L9 4"/>
      <path d="M9 11L10 20"/>

    </svg>
  );
}
