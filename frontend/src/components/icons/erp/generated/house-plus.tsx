import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HousePlusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13.22 2.41582C12.8579 2.13703 12.4113 1.99063 11.9544 2.001C11.4976 2.01137 11.0581 2.17788 10.709 2.47282L3.709 8.47182C3.4868 8.65962 3.30824 8.89363 3.18579 9.15754C3.06333 9.42144 2.99993 9.70889 3 9.99982V18.9998C3 19.5303 3.21071 20.039 3.58579 20.414C3.96086 20.7891 4.46957 20.9998 5 20.9998H19C19.5304 20.9998 20.0391 20.7891 20.4142 20.414C20.7893 20.039 21 19.5303 21 18.9998V11.6458"/>
      <path d="M15 21V13C15 12.7348 14.8946 12.4804 14.7071 12.2929C14.5196 12.1054 14.2652 12 14 12H10C9.73478 12 9.48043 12.1054 9.29289 12.2929C9.10536 12.4804 9 12.7348 9 13V21"/>
      <path d="M15 6H21"/>
      <path d="M18 3V9"/>

    </svg>
  );
}
