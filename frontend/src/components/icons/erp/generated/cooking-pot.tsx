import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CookingPotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12H22"/>
      <path d="M20 12V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V12"/>
      <path d="M4 8L20 4"/>
      <path d="M8.86 6.77955L8.41 4.96955C8.34553 4.71479 8.33189 4.44981 8.36988 4.18977C8.40787 3.92973 8.49674 3.67973 8.6314 3.45405C8.76606 3.22838 8.94388 3.03145 9.15469 2.87454C9.3655 2.71762 9.60517 2.60379 9.86 2.53955L11.8 2.05955C12.0554 1.99524 12.3211 1.98202 12.5816 2.02065C12.8422 2.05928 13.0926 2.149 13.3184 2.28466C13.5441 2.42032 13.7409 2.59925 13.8974 2.81117C14.0538 3.02309 14.1669 3.26382 14.23 3.51955L14.68 5.31955"/>

    </svg>
  );
}
