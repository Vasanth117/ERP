import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampCeilingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V7"/>
      <path d="M6 7H18L22 16H2L6 7Z"/>
      <path d="M9.17 16C9.01087 16.4524 8.96249 16.9363 9.02894 17.4112C9.09538 17.8861 9.2747 18.3382 9.55188 18.7295C9.82905 19.1208 10.196 19.44 10.6219 19.6603C11.0479 19.8806 11.5205 19.9955 12 19.9955C12.4795 19.9955 12.9521 19.8806 13.3781 19.6603C13.804 19.44 14.171 19.1208 14.4481 18.7295C14.7253 18.3382 14.9046 17.8861 14.9711 17.4112C15.0375 16.9363 14.9891 16.4524 14.83 16"/>

    </svg>
  );
}
