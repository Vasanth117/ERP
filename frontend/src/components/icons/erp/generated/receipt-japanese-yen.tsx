import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReceiptJapaneseYenIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 10L15 7"/>
      <path d="M9 7L12 10V17.5"/>
      <path d="M9 11H15"/>
      <path d="M9 15H15"/>

    </svg>
  );
}
