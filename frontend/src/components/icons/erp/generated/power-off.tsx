import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PowerOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.36 6.63965C19.4356 7.7158 20.2209 9.04708 20.6423 10.5091C21.0638 11.9711 21.1077 13.5161 20.77 14.9996"/>
      <path d="M6.16 6.16016C5.2046 6.96258 4.42648 7.95489 3.87504 9.07408C3.3236 10.1933 3.01088 11.4149 2.95675 12.6614C2.90261 13.9079 3.10824 15.152 3.56058 16.3148C4.01292 17.4776 4.70208 18.5336 5.58431 19.4158C6.46655 20.2981 7.52258 20.9872 8.68536 21.4396C9.84814 21.8919 11.0923 22.0975 12.3388 22.0434C13.5853 21.9893 14.8069 21.6766 15.9261 21.1251C17.0453 20.5737 18.0376 19.7956 18.84 18.8402"/>
      <path d="M12 2V6"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
